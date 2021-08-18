from bottle import TEMPLATE_PATH, route, run, template, redirect, get, post, request, response, auth_basic, Bottle, abort, error, static_file
import bottle
import controller
from controller import dobi_parcele_za_prikaz, dobi_info_parcele, dodaj_gosta_na_rezervacijo, naredi_rezervacijo, dobi_rezervacijo_po_id, zakljuci_na_datum_in_placaj, dobi_postavke_racuna
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
    ime = request.forms.ime#get("")
    priimek = request.forms.priimek#get("")
    emso = request.forms.emso#get("")
    drzava = request.forms.drzava#get("")
    id_parcele = request.forms.id_parcele#get("")
    od = request.forms.zacetek#get("")
    do = request.forms.konec#get("")

    print(ime, priimek)

    try:
        datum_od = dt.datetime.fromisoformat(od).date()
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
    
    r = dobi_rezervacijo_po_id(id_rezervacije)
    if not r:
        return template("error", sporocilo="Rezervacija ne obstaja!", naslov="Napaka")
    
    return template("dodajanje_gosta", id_rezervacije=id_rezervacije, today=today, tomorrow=tomorrow)

@bottle.post("/dodaj-gosta-na-rezervacijo")
def post_dodaj_gosta_na_rezervacijo():
    " V modelu rezervaciji doda gosta"

    # Preberemo lastnosti iz forme

    ime = request.forms.ime
    priimek = request.forms.priimek
    emso = request.forms.emso#get("")
    drzava = request.forms.drzava#get("")
    id_rezervacije = request.forms.rez#get("")
    od = request.forms.zacetek#get("")
    do = request.forms.konec#get("")
    try:
        datum_od = dt.datetime.fromisoformat(od).date()
        datum_do = dt.datetime.fromisoformat(do).date()
    except Exception as e:
        print(e)
        print("Napaka pri pretvorbi datumov")
        return redirect("/dodaj-gosta")


    r = dobi_rezervacijo_po_id(id_rezervacije)
    if not r:
        return template("error", sporocilo="Rezervacija ne obstaja!", naslov="Napaka")
    dodaj_gosta_na_rezervacijo(r.id_rezervacije, {
        "EMSO":emso,
        "ime":ime,
        "priimek":priimek,
        "drzava":drzava,
    },datum_od,datum_do)
    print(id_rezervacije)
    return redirect(f"/parcela/{r.id_parcele}")

@bottle.get("/predracun/<id_rezervacije>")
def predracun(id_rezervacije):
    r = dobi_rezervacijo_po_id(id_rezervacije)
    if not r:
        return template("error", sporocilo="Rezervacija ne obstaja!", naslov="Napaka")
    today = dt.date.today()
    gostje = r.gostje
    sestevek, postavke = dobi_postavke_racuna(r)
    slovar_cen = {}
    slovar_kolicin = {}
    for gost in gostje:
        slovar_kolicin[gost] = len(gost.nocitve)
        slovar_cen[gost] = format(gost.cena_nocitve() * slovar_kolicin.get(gost), '.2f')
        
        
    return template("racun", id_rezervacije=id_rezervacije, sestevek=format(sestevek, '.2f'), gostje=gostje, today=today.strftime("%d/%m/%Y"), slovar_cen=slovar_cen, slovar_kolicin=slovar_kolicin)

@bottle.get("/zakljuci/<id_rezervacije>")
def racun(id_rezervacije):
    r = dobi_rezervacijo_po_id(id_rezervacije)
    if not r:
        return template("error", sporocilo="Rezervacija ne obstaja!", naslov="Napaka")
    today = dt.date.today()
    gostje = r.gostje
    sestevek, postavke = zakljuci_na_datum_in_placaj(r, dt.date.today())
    slovar_cen = {}
    slovar_kolicin = {}
    for gost in gostje:
        slovar_kolicin[gost] = len(gost.nocitve)
        slovar_cen[gost] = format(gost.cena_nocitve() * slovar_kolicin.get(gost), '.2f')
    return template("racun", id_rezervacije=id_rezervacije, sestevek=format(sestevek, '.2f'), gostje=gostje, today=today.strftime("%d/%m/%Y"), slovar_cen=slovar_cen, slovar_kolicin=slovar_kolicin)

@bottle.error(404)
def napaka404(a):
    return template("error", sporocilo="Stran ne obstaja!", naslov="404")

@bottle.error(500)
def napaka500(a):
    return template("error", sporocilo="Napaka streznika!", naslov="500")

# if __name__=='__main__':
#     bottle.run(host='localhost', port=8080, debug=True)

bottle.run(reloader=True, debug=True)
