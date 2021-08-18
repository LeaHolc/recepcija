import json, os, datetime as dt
from typing import List, Dict,Optional

DATOTEKA_S_STANJEM="stanje.json"

NOCNINA_ZA_ODRASLE = 14.50
NOCNINA_ZA_OTROKE_OD_2_DO_14_LET = 7.25
NOCNINA_ZA_OTROKE_DO_2_LET = 0.00



TURISTICNA_TAKSA_ODRASLI = 2.00
TURISTICNA_TAKSA_OTROCI = 1.00


class Nocitev:
    def __init__(self, naziv:str, cena:float, datum):
        self.naziv = naziv
        self.cena = cena
        self.datum = datum
    
    def v_slovar(self):
        d = {
            "naziv":self.naziv,
            "cena":self.cena,
            "datum":self.datum.isoformat()
        }
        return d

    @staticmethod
    def iz_slovarja(slovar):
        datum = dt.datetime.fromisoformat(slovar['datum']).date()
        return Nocitev(slovar["naziv"], slovar['cena'], datum)


class Gost:

    def __init__(self, ime:str, priimek:str, emso:str, drzava:str, nocitve=[]):
        self.ime = ime
        self.priimek = priimek
        self.emso = emso
        self.drzava = drzava
        self.nocitve = nocitve
    
    def __repr__(self):
        return f"{self.ime} {self.priimek}"
    
    def spol(self):
        if self.emso[7:10] == '500':
            return 'M'
        else:
            return 'Ž'

    def datum_rojstva(self):
        'pretvori emso v datum rojstva'
        if self.emso[4] == "9":
            datum = dt.date(year=1000 + int(self.emso[4:7]), month=int(self.emso[2:4]), day=int(self.emso[0:2]))
            return datum
        else:
            datum = dt.date(year=2000 + int(self.emso[4:7]), month=int(self.emso[2:4]), day=int(self.emso[0:2]))
            return datum

    def starost(self):
        'izračuna starost gosta'
        datum_rojstva = self.datum_rojstva()
        danes = dt.date.today()
        razlika = danes.year - datum_rojstva.year - ((danes.month, danes.day) < (datum_rojstva.month, datum_rojstva.day))
        return razlika


    def dobi_turisticno_takso(self):
        if self.starost() < 18:
            return TURISTICNA_TAKSA_OTROCI
        else:
            return TURISTICNA_TAKSA_ODRASLI

    def dobi_naziv_in_ceno_nocitve(self):
        starost = self.starost()
        if starost < 2:
            return "NOČNINA ZA OTROKE DO 2 LET", NOCNINA_ZA_OTROKE_DO_2_LET
        elif starost >= 2 and starost < 14:
            return "NOČNINA ZA OTROKE OD 2 DO 14 LET", NOCNINA_ZA_OTROKE_OD_2_DO_14_LET
        else:
            return "NOČNINA ZA ODRASLE", NOCNINA_ZA_ODRASLE

    def cena_nocitve(self):
        cena = self.dobi_turisticno_takso() + self.dobi_naziv_in_ceno_nocitve()[1]
        return cena


    def v_slovar(self):
        d ={
            "ime":self.ime,
            "priimek":self.priimek,
            "emso":self.emso,
            "drzava":self.drzava,
            "nocitve": [s.v_slovar() for s in self.nocitve]
        }
        return d
    
    @staticmethod
    def iz_slovarja(slovar):
        nocitve = [Nocitev.iz_slovarja( s) for s in slovar.get("nocitve",[])]
        return Gost(slovar["ime"], slovar["priimek"] ,slovar['emso'], slovar["drzava"], nocitve)


class Parcela:
    def __init__(self, id_parcele, ime=None):
        self.id_parcele=str(id_parcele)
        if ime is None:
            self.ime = f"Parcela št. {id_parcele}"
        else:
            self.ime = ime 

    def v_slovar(self):
        d = {
            "id_parcele":self.id_parcele,
            "ime":self.ime
        }
        return d

    @staticmethod
    def iz_slovarja(slovar):
        return Parcela(slovar["id_parcele"], slovar.get("ime", None))

class Rezervacija:
    def __init__(self, id_rezervacije, id_parcele, gostje = []):
        self.id_rezervacije = str(id_rezervacije)
        self.id_parcele = str(id_parcele)
        self.gostje = gostje

    def __eq__(self, value:object):
        if not isinstance(value,Rezervacija): return False
        return self.id_rezervacije == value.id_rezervacije

    def v_slovar(self):
        d = {
            "id_rezervacije" : self.id_rezervacije,
            "id_parcele" : self.id_parcele,
            "gostje": [g.v_slovar() for g in self.gostje]
        }
        return d
    
    @staticmethod
    def iz_slovarja(slovar:dict):
        gostje = [Gost.iz_slovarja(s) for s in slovar.get("gostje",[])]
        return Rezervacija(slovar["id_rezervacije"], slovar["id_parcele"], gostje)

class Model:
    def __init__(self,datoteka,parcele:Dict[str,Parcela]={},rezervacije:Dict[str,Rezervacija]={}):
        self.datoteka = datoteka
        self.parcele = parcele
        self.rezervacije = rezervacije

    def vstavi_rezervacijo(self,r:Rezervacija):
        kljuc = str(r.id_rezervacije)
        if kljuc in self.rezervacije:
            return None
        self.rezervacije[kljuc] = r
        return r

    def dobi_rezervacije(self):
        return self.rezervacije.values()

    def vstavi_parcelo(self,p:Parcela):
        kljuc = str(p.id_parcele)
        if kljuc in self.parcele:
            return None
        self.parcele[kljuc] = p
        return p

    def dobi_parcele(self):
        return self.parcele
    
    @staticmethod
    def iz_datoteke(dat:str):

        ## Če datoteka še ne obstaja
        if not os.path.exists(dat):
            m= Model(dat)
            m.shrani()
            return m
        ## Preberemo datoteko
        with open(dat,encoding='utf-8') as json_file:
            try:
                data:dict = json.load(json_file)
            except json.JSONDecodeError:
                print("Napaka pri branju JSON datoteke")
                return Model(dat)
        parcele = {k:Parcela.iz_slovarja(v) for k, v in data.get("parcele", {}).items()}
        rezervacije = {k:Rezervacija.iz_slovarja(v) for k, v in data.get("rezervacije", {}).items()}
        
        return Model(dat, parcele, rezervacije)        
    
    def shrani(self):
        data = {}
        data["parcele"] = {k:v.v_slovar() for k,v in self.parcele.items()}
        data["rezervacije"] = {k:v.v_slovar() for k,v in self.rezervacije.items()}
        
        with open(self.datoteka,"w",encoding='utf-8') as write_file:
            json.dump(data,write_file,indent=4, ensure_ascii=False)
