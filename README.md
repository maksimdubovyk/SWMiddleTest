# SPARQL-запити до Wikidata

## Запит 1

Стадіони в Італії з місткістю понад 20000 та їхні офіційні сайти (стадіони без сайту теж залишаються). Топ-20 за місткістю.

```sparql
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>

SELECT ?item ?itemLabel ?value ?website WHERE {
  {
    SELECT ?item (MAX(?cap) AS ?value) (SAMPLE(?site) AS ?website) WHERE {
      ?item wdt:P31 wd:Q483110 ;
            wdt:P17 wd:Q38 ;
            wdt:P1083 ?cap .
      FILTER(?cap > 20000)
      OPTIONAL { ?item wdt:P856 ?site . }
    }
    GROUP BY ?item
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY DESC(?value) ?item
LIMIT 20
```

## Запит 2

Регіони Італії, де щонайменше 3 стадіони. Топ-10 за кількістю стадіонів.

```sparql
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>

SELECT ?region ?regionLabel ?cnt WHERE {
  {
    SELECT ?region (COUNT(DISTINCT ?item) AS ?cnt) WHERE {
      ?item wdt:P31 wd:Q483110 ;
            wdt:P17 wd:Q38 ;
            wdt:P131 ?region .
    }
    GROUP BY ?region
    HAVING (COUNT(DISTINCT ?item) >= 3)
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY DESC(?cnt) ?region
LIMIT 10
```

## Запит 3

Стадіони в Італії та населення регіону, де вони розташовані. Топ-10 за населенням.

```sparql
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>

SELECT ?item ?itemLabel ?region ?regionLabel ?population WHERE {
  {
    SELECT ?item (SAMPLE(?r) AS ?region) (MAX(?pop) AS ?population) WHERE {
      ?item wdt:P31 wd:Q483110 ;
            wdt:P17 wd:Q38 ;
            wdt:P131 ?r .
      ?r wdt:P1082 ?pop .
      FILTER NOT EXISTS {
        ?item wdt:P131 ?r2 .
        ?r2 wdt:P1082 ?pop2 .
        FILTER(?pop2 > ?pop)
      }
    }
    GROUP BY ?item
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY DESC(?population) ?item
LIMIT 10
```
