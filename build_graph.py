import csv
import json
import sys
from collections import Counter
from datetime import datetime
from decimal import Decimal

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD

EX = Namespace("http://example.org/mkr/")


def iri(kind, name):
    return URIRef(EX + f"{kind}/{name.strip().replace(' ', '_')}")


def norm_id(s):
    return s.strip().upper()


def norm_city(s):
    return s.strip().title()


def parse_date(s):
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Невідомий формат дати: {s!r}")


def parse_note(note):
    parts = dict(p.split("=", 1) for p in note.strip().split(";") if "=" in p)
    if "delay" not in parts:
        return None
    return int(parts["delay"].strip()), parts.get("by", "").strip() or None


def read_flights(path):
    flights = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fid = norm_id(row["flight_id"])
            if not fid or fid in flights:
                continue
            price = row["price_eur"].strip()
            flights[fid] = {
                "id": fid,
                "airline": row["airline"].strip(),
                "from_city": norm_city(row["from_city"]),
                "from_country": row["from_country"].strip(),
                "to_city": norm_city(row["to_city"]),
                "to_country": row["to_country"].strip(),
                "date": parse_date(row["dep_date"]),
                "duration": int(row["duration_min"].strip()),
                "price": Decimal(price) if price else None,
                "delay": parse_note(row["note"] or ""),
            }
    return list(flights.values())


def add_schema(g):
    for cls in ("Flight", "Airline", "City", "Country", "Source"):
        g.add((EX[cls], RDF.type, RDFS.Class))
    for sub in ("BudgetFlight", "LongFlight"):
        g.add((EX[sub], RDF.type, RDFS.Class))
        g.add((EX[sub], RDFS.subClassOf, EX.Flight))

    props = {
        "operatedBy": (EX.Flight, EX.Airline),
        "departsFrom": (EX.Flight, EX.City),
        "arrivesAt": (EX.Flight, EX.City),
        "locatedIn": (EX.City, EX.Country),
        "departureDate": (EX.Flight, XSD.date),
        "durationMin": (EX.Flight, XSD.integer),
        "priceEur": (EX.Flight, XSD.decimal),
        "hasDelayMinutes": (EX.Flight, XSD.integer),
        "reportedBy": (RDF.Statement, EX.Source),
        "fromBusyCountry": (EX.Flight, XSD.boolean),
    }
    for name, (domain, rng) in props.items():
        g.add((EX[name], RDF.type, RDF.Property))
        g.add((EX[name], RDFS.domain, domain))
        g.add((EX[name], RDFS.range, rng))


def add_labeled(g, kind, cls, name):
    node = iri(kind, name)
    g.add((node, RDF.type, cls))
    g.add((node, RDFS.label, Literal(name, lang="en")))
    return node


def build(flights, params):
    g = Graph()
    g.bind("ex", EX)
    g.bind("xsd", XSD)
    add_schema(g)

    budget = Decimal(str(params["budget_threshold_eur"]))
    long_min = int(params["long_flight_min"])
    dep_count = Counter(fl["from_country"] for fl in flights)

    for fl in flights:
        node = iri("flight", fl["id"])

        types = []
        if fl["price"] is not None and fl["price"] <= budget:
            types.append(EX.BudgetFlight)
        if fl["duration"] >= long_min:
            types.append(EX.LongFlight)
        for t in types or [EX.Flight]:
            g.add((node, RDF.type, t))

        airline = add_labeled(g, "airline", EX.Airline, fl["airline"])
        g.add((node, EX.operatedBy, airline))

        for prop, city_key, country_key in (
            (EX.departsFrom, "from_city", "from_country"),
            (EX.arrivesAt, "to_city", "to_country"),
        ):
            city = add_labeled(g, "city", EX.City, fl[city_key])
            country = add_labeled(g, "country", EX.Country, fl[country_key])
            g.add((city, EX.locatedIn, country))
            g.add((node, prop, city))

        g.add((node, EX.departureDate, Literal(fl["date"].isoformat(), datatype=XSD.date)))
        g.add((node, EX.durationMin, Literal(fl["duration"], datatype=XSD.integer)))
        if fl["price"] is not None:
            g.add((node, EX.priceEur, Literal(fl["price"], datatype=XSD.decimal)))

        if fl["delay"]:
            minutes, source = fl["delay"]
            stmt = iri("stmt", f"{fl['id']}-delay")
            g.add((stmt, RDF.type, RDF.Statement))
            g.add((stmt, RDF.subject, node))
            g.add((stmt, RDF.predicate, EX.hasDelayMinutes))
            g.add((stmt, RDF.object, Literal(minutes, datatype=XSD.integer)))
            if source:
                src = iri("source", source)
                g.add((src, RDF.type, EX.Source))
                g.add((src, RDFS.label, Literal(source, lang="en")))
                g.add((stmt, EX.reportedBy, src))

        if dep_count[fl["from_country"]] >= 2:
            g.add((node, EX.fromBusyCountry, Literal(True, datatype=XSD.boolean)))

    return g


def main(argv):
    if len(argv) != 4:
        sys.exit("Використання: python build_graph.py flights.csv params.json graph.ttl")
    csv_path, params_path, out_path = argv[1:]
    with open(params_path, encoding="utf-8") as f:
        params = json.load(f)
    flights = read_flights(csv_path)
    g = build(flights, params)
    g.serialize(destination=out_path, format="turtle")
    print(f"{out_path}: {len(flights)} рейсів, {len(g)} тріплетів")


if __name__ == "__main__":
    main(sys.argv)
