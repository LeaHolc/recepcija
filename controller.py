import datetime as dt
from model import Model, Rezervacija, Gost, Parcela, Nocitev
from typing import Tuple, List

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
    for id_res, rezervacija in model.rezervacije.items():
        if rezervacija.id_parcele==id_parcela:
            gosti_ta_dan = []
            for gost in rezervacija.gostje:
                for storitev in gost.nocitve:
                    if storitev.datum==datum:
                        gosti_ta_dan.append(gost)
            if len(gosti_ta_dan):
                return rezervacija, gosti_ta_dan
    return None, []

def dodaj_gosta_na_rezervacijo(rid, lastnosti_gosta, datum_od, datum_do):
    'Doda novega gosta v podatkovno bazo in vrne novi objekt'

    # drugace naredimo novo osebo
    g = Gost(    
        lastnosti_gosta['ime'],
        lastnosti_gosta['priimek'],
        lastnosti_gosta["EMSO"],
        lastnosti_gosta['drzava'])
    
    # Gsotu dodamo storitve
    naziv_nocitve, cena_nocitve = g.dobi_naziv_in_ceno_nocitve()
    cena_nocitve += g.dobi_turisticno_takso()

    trenutni_datum = datum_od
    while trenutni_datum < datum_do:
        g.nocitve.append(
            Nocitev(naziv_nocitve, cena_nocitve, trenutni_datum)
        )
        trenutni_datum += dt.timedelta(days=1)

    model.rezervacije[rid].gostje.append(g)
    # Vstavimo v bazo
    model.shrani()
    return g

def dobi_nov_id_rezervacije():
    if not len(model.rezervacije): return "1"
    najvecji_idx = max([int(rid) for rid in model.rezervacije])
    return str(najvecji_idx+1)

def naredi_rezervacijo( id_parcele):
    novi_id_rezervacije = dobi_nov_id_rezervacije()
    r = Rezervacija(novi_id_rezervacije, id_parcele)
    model.vstavi_rezervacijo(r)
    return r

def dobi_postavke_racuna(r:Rezervacija):
    postavke = []
    sestevek = 0
    for g in r.gostje:
        for s in g.nocitve:
            postavke.append(str((s.naziv, s.cena)))
            sestevek += s.cena
    return sestevek, postavke

def zakljuci_na_datum_in_placaj(r:Rezervacija, datum_zakljucka:dt.date):
    " Gostom naredi seznam novih nocitev, do datuma zakljucka in rezervacijo zakljuci"
    for g in r.gostje:
        nove_nocitve = []
        for nocitev in g.nocitve:
            if nocitev.datum <= datum_zakljucka:
                nove_nocitve.append(nocitev)       
        g.nocitve = nove_nocitve

    postavke = dobi_postavke_racuna(r)
    del model.rezervacije[r.id_rezervacije]
    model.shrani()

    return postavke

def dobi_rezervacijo_po_id(rid):
    " controller je posrednik za dostop streznika do modela "
    return model.rezervacije[rid]