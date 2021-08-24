import json, os, datetime as dt

DATOTEKA_S_STANJEM="stanje.json"

NOCNINA_ZA_ODRASLE = 14.50
NOCNINA_ZA_OTROKE_OD_2_DO_14_LET = 7.25
NOCNINA_ZA_OTROKE_DO_2_LET = 0.00

TURISTICNA_TAKSA_ODRASLI = 2.00
TURISTICNA_TAKSA_OTROCI = 1.00

class Nocitev:

    def __init__(self, naziv, cena, datum):
        self.naziv = naziv
        self.cena = cena
        self.datum = datum
    
    def v_slovar(self):
        return {
            "naziv":self.naziv,
            "cena":self.cena,
            "datum":self.datum.isoformat()
        }

    @staticmethod
    def iz_slovarja(slovar):
        datum = dt.datetime.fromisoformat(slovar['datum']).date()
        return Nocitev(slovar["naziv"], slovar['cena'], datum)

class Gost:

    def __init__(self, ime, priimek, emso, drzava, nocitve=[]):
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
        return {
            "ime":self.ime,
            "priimek":self.priimek,
            "emso":self.emso,
            "drzava":self.drzava,
            "nocitve": [nocitev.v_slovar() for nocitev in self.nocitve]
        }
    
    @staticmethod
    def iz_slovarja(slovar):
        nocitve = [Nocitev.iz_slovarja(nocitev) for nocitev in slovar.get("nocitve", [])]
        return Gost(slovar["ime"], slovar["priimek"], slovar['emso'], slovar["drzava"], nocitve)

class Parcela:
    def __init__(self, id_parcele, ime=None):
        self.id_parcele=str(id_parcele)
        if ime is None:
            self.ime = f"Parcela št. {id_parcele}"
        else:
            self.ime = ime 

    def v_slovar(self):
        return {
            "id_parcele":self.id_parcele,
            "ime":self.ime
        }

    @staticmethod
    def iz_slovarja(slovar):
        return Parcela(slovar["id_parcele"], slovar.get("ime", None))

class Rezervacija:
    def __init__(self, id_rezervacije, id_parcele, gostje = []):
        self.id_rezervacije = str(id_rezervacije)
        self.id_parcele = str(id_parcele)
        self.gostje = gostje

    def __eq__(self, podatki):
        "preveri, ali podatki določajo rezervacijo"
        if not isinstance(podatki, Rezervacija): 
            return False
        else:
            return self.id_rezervacije == podatki.id_rezervacije

    def v_slovar(self):
        return {
            "id_rezervacije" : self.id_rezervacije,
            "id_parcele" : self.id_parcele,
            "gostje": [gost.v_slovar() for gost in self.gostje]
        }
    
    @staticmethod
    def iz_slovarja(slovar):
        gostje = [Gost.iz_slovarja(gost) for gost in slovar.get("gostje", [])]
        return Rezervacija(slovar["id_rezervacije"], slovar["id_parcele"], gostje)

class Model:
    def __init__(self, datoteka, parcele={}, rezervacije={}):
        self.datoteka = datoteka
        self.parcele = parcele
        self.rezervacije = rezervacije

    def vstavi_rezervacijo(self, rezervacija):
        kljuc = str(rezervacija.id_rezervacije)
        if kljuc in self.rezervacije:
            return None
        self.rezervacije[kljuc] = rezervacija
        return rezervacija

    def dobi_rezervacije(self):
        return self.rezervacije.values()

    def vstavi_parcelo(self, parcela):
        kljuc = str(parcela.id_parcele)
        if kljuc in self.parcele:
            return None
        self.parcele[kljuc] = parcela
        return parcela

    def dobi_parcele(self):
        return self.parcele
    
    @staticmethod
    def iz_datoteke(datoteka):

        ## Če datoteka še ne obstaja
        if not os.path.exists(datoteka):
            m = Model(datoteka)
            m.shrani()
            return m

        ## Preberemo datoteko
        with open(datoteka, encoding='utf-8') as dat:
            try:
                data = json.load(dat)
            except json.JSONDecodeError:
                print("Napaka pri branju JSON datoteke")
                return Model(datoteka)

        parcele = {stevilka:Parcela.iz_slovarja(lastnosti) for stevilka, lastnosti in data.get("parcele", {}).items()}
        rezervacije = {stevilka:Rezervacija.iz_slovarja(lastnosti) for stevilka, lastnosti in data.get("rezervacije", {}).items()}
        
        return Model(datoteka, parcele, rezervacije)        
    
    def shrani(self):
        data = {}
        data["parcele"] = {stevilka:lastnosti.v_slovar() for stevilka, lastnosti in self.parcele.items()}
        data["rezervacije"] = {stevilka:lastnosti.v_slovar() for stevilka, lastnosti in self.rezervacije.items()}
        
        with open(self.datoteka,"w", encoding='utf-8') as write_file:
            json.dump(data, write_file, indent=4, ensure_ascii=False)
