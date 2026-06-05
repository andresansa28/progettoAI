import re

def calcola_fairness(solver, termini_obiettivo, lavoratori):
    punteggi = {}
    #assegnamento al dizioantio il punteggio di zero per ogni lavoratore (inizialmente)cosi poi si può iniziare a popolare
    for i in range(lavoratori):
        punteggi[i] = 0

    for term in termini_obiettivo:
        punteggio = solver.Value(term)
        if punteggio == 0:
            continue #se il punteggio assegnato è zero non vale la pena fare altri calcoli

        stringa_termine = str(term)  #per convertire l'oggetto di ortools in una stringa per poi estrapolare il alvoreaore
        
        match = re.search(r"l(\d+)_", stringa_termine) #estrae solo l'identificatvo del lavoreare per aggiornare il sui punteggio nel dizionre
        #print(match)
        if match:
            lavoratore = int(match.group(1)) 
            punteggi[lavoratore] += punteggio
        
    punteggi_ordinati = dict(sorted(punteggi.items(), key=lambda item: item[1]))
    return punteggi_ordinati