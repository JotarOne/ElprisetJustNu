# ElprisetJustNu
Home Assistant custom component for swedish customer to fetch electricity prices from the api Elpriset just nu.

## In Swedish
Detta är en integration för att hämta aktuellt pris och snittpris för dagen från [Elpriset just nu](https://www.elprisetjustnu.se/)
Integrationen är gjord för att underlätta för mig personligen och försöka minska på antalet anrop till tjänstens API.

Tanken är att försöka hämta morgondagens priser i tid före midnatt, så de finns på plats och kan uppdateras snart efter.
Det gör att man slipper (i teorin9 vara beroende av hur ofta t ex rest-sensorer behöver uppdatera.

Om den kan hjälpa någon annan är det bara trevligt, men **obs!** jag lämnar inga garantier :smile:

Inställningar finns för elprisområde och hur ofta ny information ska laddas från API.
