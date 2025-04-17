def clausula_L(combinacoes, caminho):
    verifica = ""
    for conj in combinacoes:
        for elemento in conj:
            verifica += f"{elemento} "
        verifica += "0\n"
        with open(caminho, 'a') as file:
            file.write(verifica)
        verifica=""