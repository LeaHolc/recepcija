from bottle import TEMPLATE_PATH, route, run, template, redirect, get, post, request, response, auth_basic, Bottle, abort, error
import bottle
from typing import List, Dict,Optional
import controller
from controller import dobi_parcele_za_prikaz, \
    dobi_info_parcele, dodaj_gosta_na_rezervacijo, naredi_rezervacijo, dobi_rezervacijo_po_id, zakljuci_na_datum_in_placaj, dobi_postavke_racuna
import datetime as dt

@bottle.get('/')
def root():
    redirect('/domov')

@bottle.get('/domov')
def index():
    parcele = dobi_parcele_za_prikaz(dt.date.today())
    return template("domov", parcele=parcele, hide_header_back=True)

@bottle.get("/parcela/<id_parcele>")
def parcela(id_parcele):
    'Preverimo stanje parcele'
    rez, gostje = dobi_info_parcele(id_parcele, dt.date.today())
    if rez is not None:
        # Parcela je trenutno zasedena
        stanje = "Parcela je trenutno zasedena"
    else:
        stanje = "Parcela je trenutno na voljo"
    return template('parcela', id_parcela=id_parcele, rezervacija=rez, stanje=stanje, gostje=gostje)


@bottle.get("/naredi-rezervacijo/<id_parcele>")
def nova_rezervacija(id_parcele=None):
    print(id_parcele)
    today = dt.date.today()
    tomorrow = today + dt.timedelta(days=1)
    return template('nova_rezervacija', id_parcele=id_parcele, today=today, tomorrow=tomorrow)

@bottle.post("/naredi-rezervacijo")
def naredi_novo_rezervacijo():
    " V modelu naredi novo rezervacijo in ji doda prvega gosta"

    # Preberemo lastnosti iz forme
    ime = request.forms.get("ime")
    priimek = request.forms.get("priimek")
    emso = request.forms.get("emso")
    drzava = request.forms.get("drzava")
    id_parcele = request.forms.get("id_parcele")
    od = request.forms.get("zacetek")
    do = request.forms.get("konec")
    datum_od = dt.date.today()
    try:
        datum_do = dt.datetime.fromisoformat(do).date()
    except Exception as e:
        print(e)
        print("Napaka pri pretvorbi datumov")
        return redirect("/naredi-rezervacijo")
    
    r = naredi_rezervacijo(id_parcele)
    dodaj_gosta_na_rezervacijo(r.id_rezervacije, {
        "EMSO":emso,
        "ime":ime,
        "priimek":priimek,
        "drzava":drzava,
    },datum_od,datum_do)
    return redirect(f"/parcela/{id_parcele}")

@bottle.get("/dodaj-gosta/<id_rezervacije>")
def get_dodaj_gosta_na_rezervacijo(id_rezervacije):
    today = dt.date.today()
    tomorrow = today + dt.timedelta(days=1)
    return template("dodajanje_gosta", id_rezervacije=id_rezervacije, today=today, tomorrow=tomorrow)

@bottle.post("/dodaj-gosta-na-rezervacijo")
def post_dodaj_gosta_na_rezervacijo():
    " V modelu rezervaciji doda gosta"

    # Preberemo lastnosti iz forme
    ime = request.forms.get("ime")
    priimek = request.forms.get("priimek")
    emso = request.forms.get("emso")
    drzava = request.forms.get("drzava")
    id_rezervacije = request.forms.get("rez")
    od = request.forms.get("zacetek")
    do = request.forms.get("konec")
    datum_od = dt.date.today()
    try:
        datum_do = dt.datetime.fromisoformat(do).date()
    except Exception as e:
        print(e)
        print("Napaka pri pretvorbi datumov")
        return redirect("/dodaj-gosta")


    r = dobi_rezervacijo_po_id(id_rezervacije)
    dodaj_gosta_na_rezervacijo(r.id_rezervacije, {
        "EMSO":emso,
        "ime":ime,
        "priimek":priimek,
        "drzava":drzava,
    },datum_od,datum_do)
    print(id_rezervacije)
    return redirect(f"/parcela/{r.id_parcele}")

@bottle.get("/predracun/<id_rezervacije>")
def racun(id_rezervacije):
    r = dobi_rezervacijo_po_id(id_rezervacije)
    sestevek, postavke = dobi_postavke_racuna(r)
    return postavke

@bottle.get("/zakljuci/<id_rezervacije>")
def racun(id_rezervacije):
    r = dobi_rezervacijo_po_id(id_rezervacije)
    if not r:
        return template("error", sporocilo="Rezervacija ne obstaja!", naslov="Napaka")
    sestevek, postavke = zakljuci_na_datum_in_placaj(r, dt.date.today())
    return postavke

@bottle.error(404)
def napaka404(a):
    return template("error", sporocilo="Stran ne obstaja!", naslov="404")


@bottle.error(500)
def napaka500(a):
    return template("error", sporocilo="Napaka streznika!", naslov="500")


if __name__=='__main__':
    bottle.run(host='localhost', port=8080, debug=True)
