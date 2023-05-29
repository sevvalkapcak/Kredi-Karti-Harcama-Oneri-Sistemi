import dbm
import tkinter as tk
import tkinter.filedialog as fd
import pandas as pd
import tkinter.messagebox as msgbox
from recommendations import *
import pickle as pk


KULLANICI_ISMI = 'Sevval'

class TumEkran(tk.Frame):
    ''' Butun ekran bilesenlerinin oldugu sinif. 

        Kullanici harcamalari dosyasini girdirir ve diger ekran bilesenlerini olusturur (composition).

    '''
    
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.initGui()
        self.df = pd.DataFrame()
        self.pack()

        self.giris = GirisEkrani(parent)
        self.oneri = OneriEkrani(parent, self.giris)

    def initGui(self):
        self.yukle_label = tk.Label(self, text="Yandaki butonu kullanarak diger kullanicilari yukleyebilirsiniz:")
        self.yukle_buton = tk.Button(self, text="Csv Dosya Sec", command=self.aktar)

        self.yukle_label.pack(side=tk.LEFT)
        self.yukle_buton.pack(side=tk.RIGHT)

    def aktar(self):
        file_name = fd.askopenfilename()
        self.df = pd.read_csv(file_name)
        #print(self.df.head())
        self.giris.populate_liste(self.df)


class GirisEkrani(tk.Frame):
    ''' Kullanici harcamalarinin girildigi giris ekrani.

        Populate_liste fonksiyonu ile disaridan kategori girilmesini saglar. Kullanici harcamalarini tum_harcamalar isimli db ye yazar.

    '''

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.sozluk = {}
        self.kategoriler = []
        self.magazalar = []
        self.initGui()
        self.pack()

    def initGui(self):
        self.ana_label = tk.Label(
            self, text="Kullanici Bilgileri Gir", font='Helvetica 18 bold')
        

        self.kategori_label = tk.Label(
            self, text="Kategoriler")

        # exportselection=0: Arada mouse ile secilen eleman kaybolmasin diye
        self.kategori_lb = tk.Listbox(
            self, selectmode="single", width=30, exportselection=0)

        self.kullanici_label = tk.Label(
            self, text="Kullanici Harcamalari")
        self.kullanici_lb = tk.Listbox(self, selectmode="single", width=40)

        self.label_miktar = tk.Label(self, text="Toplam Miktar")
        
        self.var_miktar = tk.StringVar()
        self.text_miktar = tk.Entry(self, textvariable=self.var_miktar)

        self.ekle_buton = tk.Button(
            self, text="Harcama Gir", command=self.harcama_ekle_func)

        self.kullanici_harcama_oku()


    
        self.ana_label.grid(row = 0, column = 0, columnspan=4)

        self.kategori_label.grid(row=1, column=0)
        self.kategori_lb.grid(row=2, column=0, rowspan=2)

        self.label_miktar.grid(row=1, column=1)
        self.text_miktar.grid(row=2, column=1)
        self.ekle_buton.grid(row=2, column=2)

        self.kullanici_label.grid(row=1, column=3)
        self.kullanici_lb.grid(row=2, column=3, rowspan=2)

    def kullanici_harcama_oku(self):
        ''' DB ye daha once yazilmis harcamalari okur ve ilgili listeye yazar.
        '''

        db = dbm.open("tum_harcamalar", "c")
        self.kullanici_lb.delete(0,tk.END)
        try:
            sozluk = pk.loads(db[KULLANICI_ISMI])
        except:
            raise Exception('DB dosyasi buldum ama kullanici bulamadim?')
            db.close()
            return

        for key, value in sozluk.items():
            self.kullanici_lb.insert(tk.END, '{}: {}'.format(key, value))
        self.sozluk[KULLANICI_ISMI] = sozluk
        #print(keys, sozluk)
        db.close()
                
    def harcama_ekle_func(self):
        kategori = self.kategori_lb.curselection()
        if len(kategori) < 1:
            msgbox.showerror(title="Oneri hatasi",
                             message="En az bir kategori secilmeli")
            return

        db = dbm.open("tum_harcamalar", "c")
        try:
            user_ratings = pk.loads(db[KULLANICI_ISMI])
        except KeyError:
            print("Daha once bu kullanici icin bilgi girilmemis. Yeni bir sozluk olusturuluyor")
            user_ratings = dict()

        user_ratings[self.kategoriler[kategori[0]]] = float(self.var_miktar.get())
      
        db[KULLANICI_ISMI] = pk.dumps(user_ratings)
        db.close()

        # DB doldurulduktan sonra listeye eklemek icin db den okuma fonksiyonunu cagir!
        self.kullanici_harcama_oku()



    def populate_liste(self, data):
        self.preprocess(data)
        for i, v in enumerate(self.kategoriler):
            self.kategori_lb.insert(i, v)



 

    def preprocess(self, df: pd.DataFrame):
        if len(df) is 0:
            return

        companies = {item for item in df['Company']}
        accounts = {item for item in df['Account']}
        
        cards = dict()
        for comp in companies:
            cards[comp] = {}
            for ac in accounts:
                cards[comp][ac] = 0.0

        for index, row in df.iterrows():
            comp, acco = row['Company'], row['Account']
            value = row['JV Value'] if row['JV Value'] > 0 else 0
            cards[comp][acco] += value

        # Clean 0.0 entries
        cleaned = {}
        for comp in cards.keys():
            cleaned[comp] = {}
            for key, val in cards[comp].items():
                if val > 1E-3:
                    cleaned[comp][key] = val

        self.sozluk = cleaned
        self.kategorileri_al()
        self.magazalari_al()
        self.kullanici_harcama_oku()

    def magazalari_al(self):
        self.magazalar = list(self.sozluk.keys())

    def kategorileri_al(self):
        if len(self.sozluk.keys())>1:
            self.kategoriler = list({item for sublist in [list(x.keys())
                                    for x in self.sozluk.values()] for item in sublist})

class OneriEkrani(tk.Frame):
    ''' Oneri elemanlarinin oldugu ekran.

        recommendations.py da uygulanmis fonksiyonlari kullanicinin sectigi sekilde cagirir. Giris ekrani icindeki sozluk degiskenine erisebilir.

    '''

    def __init__(self,parent, giris):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.parent = parent
        self.giris_ekrani = giris
        self.initGui()
        self.pack()

    def initGui(self):
        self.ana_label = tk.Label(
            self, text="Oneri Ekrani", font='Helvetica 18 bold')

        self.rb_frame = tk.Frame(self)
        self.kategori_secili = tk.BooleanVar()
        self.kategori_secili.set(True)

        self.oneri_label = tk.Label(
            self, text="Oneriler:")
        self.oneri_lb = tk.Listbox(self, selectmode="single", width=40)

        self.benzer_label = tk.Label(
            self, text="Magazalar:")
        self.benzer_lb = tk.Listbox(self, selectmode="single", width=40)

        true_button = tk.Radiobutton(self,
                        text="Kategori-Tabanli-Oneri",
                        variable=self.kategori_secili,
                        value=True
                        )

        false_button = tk.Radiobutton(self,
                                text="Firma-Tabanli-Oneri",
                                      variable=self.kategori_secili,
                                value=False
                                )

        self.oneri_buton = tk.Button(
            self, text="Oneri Yap", command=self.oneri_func)

        self.benzer_buton = tk.Button(
            self, text="Benzer Magaza Bul", command=self.benzer_func)


        self.ana_label.grid(row=0, column=0, columnspan = 4)
        true_button.grid(row=2, column=0, sticky='w')
        false_button.grid(row=3, column=0, sticky='w')

        self.oneri_buton.grid(row=2, column=1)
        self.benzer_buton.grid(row=3, column=1)

        self.oneri_label.grid(row=1, column=2)
        self.oneri_lb.grid(row=2, column=2, rowspan=3)

        self.benzer_label.grid(row=1, column=3)
        self.benzer_lb.grid(row=2, column=3, rowspan=3)

    def oneri_func(self):
        oneri_sozluk = self.giris_ekrani.sozluk
        if self.kategori_secili.get():
            recommendations = getRecommendations(
                oneri_sozluk, KULLANICI_ISMI, similarity=sim_cosine)
        else:
            itemMatch = calculateSimilarItems(
                oneri_sozluk, KULLANICI_ISMI,  similarity=sim_cosine)
            recommendations = getRecommendedItems(
                oneri_sozluk, itemMatch, KULLANICI_ISMI)

        self.oneri_lb.delete(0, tk.END)
        for i in range(0, min(3, len(recommendations))):
            self.oneri_lb.insert(i, '{} -> {}'.format(recommendations[i][1], recommendations[i][0]))

    def benzer_func(self):
        dene = self.giris_ekrani.sozluk
        matches = topMatches(dene, KULLANICI_ISMI)


        self.benzer_lb.delete(0, tk.END)
        for i in range(0, min(3, len(matches))):
            self.benzer_lb.insert(
                i, '{} -> {}'.format(matches[i][1], matches[i][0]))



def __main__():
    
    root = tk.Tk()
    root.title("Harcama Oneri Sistemi")
    #root.geometry("650x650+400+100")
    
    TumEkran(root)

    root.mainloop()


__main__()
