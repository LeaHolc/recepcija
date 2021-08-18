import datetime as dt
from model import Model, Rezervacija, Gost, Parcela, Nocitev

model = Model.iz_datoteke("stanje.json")
print(f"Model povezan z datoteko '{model.datoteka}'")

def dobi_parcele_za_prikaz(datum):
    'Vrne seznam parcel (idParcela, idRezervacija), če nima rezervacije je drugo polje None'
    seznam_parcel = model.dobi_parcele()
    seznam = [
        [pid, parc.ime, dobi_info_parcele(pid, datum)[0] is not None] for pid, parc in seznam_parcel.items() ]
    return seznam

def dobi_info_parcele(id_parcela, datum):
    'Vrne rezervacijo (ce obstaja) parcele za datum'
    for id_rez, rezervacija in model.rezervacije.items():
        if rezervacija.id_parcele == id_parcela:
            gosti_ta_dan = []
            for gost in rezervacija.gostje:
                for storitev in gost.nocitve:
                    if storitev.datum == datum:
                        gosti_ta_dan.append(gost)
            if len(gosti_ta_dan):
                return rezervacija, gosti_ta_dan
    return None, []

def dodaj_gosta_na_rezervacijo(rid, lastnosti_gosta, datum_od, datum_do):
    'Doda novega gosta v podatkovno bazo in vrne novi objekt'

    gost_na_parceli = Gost(    
        lastnosti_gosta['ime'],
        lastnosti_gosta['priimek'],
        lastnosti_gosta["EMSO"],
        lastnosti_gosta['drzava'], [])
    
    # Gostu dodamo storitve
    naziv_nocitve, cena_nocitve = gost_na_parceli.dobi_naziv_in_ceno_nocitve()
    cena_nocitve += gost_na_parceli.dobi_turisticno_takso()


    trenutni_datum = datum_od
    while trenutni_datum < datum_do: 
        gost_na_parceli.nocitve.append(Nocitev(naziv_nocitve, cena_nocitve, trenutni_datum))
        trenutni_datum += dt.timedelta(days=1)
    model.rezervacije[rid].gostje.append(gost_na_parceli)
    # Vstavimo v bazo
    model.shrani()
    return gost_na_parceli

def dobi_nov_id_rezervacije():
    "pogleda največji indeks že ustvarjene rezervacije in ustvari novega kot indeks največje plus 1"
    if len(model.rezervacije) == 0: 
        return "1"
    else:
        maksimalni = int(list(model.rezervacije.keys())[0])
        for rezervacija_id in model.rezervacije:
            num_id = int(rezervacija_id)
            if num_id > maksimalni:
                maksimalni = num_id

    return str(maksimalni + 1)

def naredi_rezervacijo(id_parcele):
    novi_id_rezervacije = dobi_nov_id_rezervacije()
    nova_rezervacija = Rezervacija(novi_id_rezervacije, id_parcele)
    model.vstavi_rezervacijo(nova_rezervacija)
    return nova_rezervacija

def dobi_postavke_racuna(rezervacija):
    postavke = []
    sestevek = 0
    for gost in rezervacija.gostje:
        for storitev in gost.nocitve:
            postavke.append(str((storitev.naziv, storitev.cena)))
            sestevek += storitev.cena
    return sestevek, postavke

def zakljuci_na_datum_in_placaj(rezervacija, datum_zakljucka):
    " Gostom naredi seznam novih nocitev, do datuma zakljucka in rezervacijo zakljuci"
    for gost in rezervacija.gostje:
        nove_nocitve = []
        for nocitev in gost.nocitve:
            if nocitev.datum < datum_zakljucka:
                nove_nocitve.append(nocitev)       
        gost.nocitve = nove_nocitve

    postavke = dobi_postavke_racuna(rezervacija)
    del model.rezervacije[rezervacija.id_rezervacije]
    model.shrani()

    return postavke

def dobi_rezervacijo_po_id(rezervacija_id):
    " controller je posrednik za dostop streznika do modela "
    return model.rezervacije.get(rezervacija_id, None)