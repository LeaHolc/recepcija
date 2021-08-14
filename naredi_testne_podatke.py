from model import Model, Nocitev, Gost, Rezervacija, Parcela
import datetime as dt

### To se izvede samo, kadar datoteko neposredno kličemo s `python model.py`
m = Model.iz_datoteke("stanje.json")

for i in range(1,11):
    m.vstavi_parcelo(Parcela(i))

g = Gost('Lea','Holc', '2101001505244', 'SI', [
    Nocitev("NOCITEV ODRASLI", 14.5, dt.date.today()-dt.timedelta(days=1)),
    Nocitev("NOCITEV ODRASLI", 14.5, dt.date.today()),
    Nocitev("NOCITEV ODRASLI", 14.5, dt.date.today()+dt.timedelta(days=1)),
    Nocitev("NOCITEV ODRASLI", 14.5, dt.date.today()+dt.timedelta(days=2))
])
m.shrani()
r = Rezervacija(1, 2, [g])
m.vstavi_rezervacijo(r)
m.shrani()
print("Testni podatki so bili ustvarjeni!")