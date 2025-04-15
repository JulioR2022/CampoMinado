#!/bin/bash
declare -A VAR
L=4
C=4
TOTVARS=1

# Enumera cada proposição com um número única para cada posição da matriz
for((i=0;i<L;i++)); do
        for((j=0;j<C;j++)); do
                VAR[B,$i,$j]=$TOTVARS
                VAR[r,$TOTVARS]=B,$i,$j
                ((TOTVARS++))
                VAR[P,$i,$j]=$TOTVARS
                VAR[r,$TOTVARS]=P,$i,$j
                ((TOTVARS++))
                VAR[S,$i,$j]=$TOTVARS
                VAR[r,$TOTVARS]=S,$i,$j
                ((TOTVARS++))
                VAR[W,$i,$j]=$TOTVARS
                VAR[r,$TOTVARS]=W,$i,$j
                ((TOTVARS++))
        done
done

# Vamos precisar criar uma formulá diferente, ler o material no site
#formula da brisa x poço
# (\lnot Bx,y \lor Px-1,y \lor Px+1,y \lor Px,y-1 \lor Px,y+1)
# (Bx,y \lor \lnot Px-1,y)
# (Bx,y \lor \lnot Px+1,y)
# (Bx,y \lor \lnot Px,y-1)
# (Bx,y \lor \lnot Px,y+1)

# Apenas retorna os adjacentes de uma posição
function adjacentes()
{
        local l=$1
        local c=$2
        local t=$3
        [[ -z "$t" ]] && t=P
        dl=(0  0 -1 1)
        dc=(-1 1  0 0)
        local x
        for((x=0;x<${#dl[@]};x++)); do
                nl=$((l+${dl[$x]}))
                nc=$((c+${dc[$x]}))
                if ((nl<0 ))|| ((nl>=L)); then
                        continue;
                fi
                if ((nc<0 ))|| ((nc>=C)); then
                        continue;
                fi
                echo -n " ${VAR[$t,$nl,$nc]}"
        done

}

# Escreve as clausúlas no arquivo para o SatSolver resolver depois
CLAUSULAS=0
for((i=0;i<L;i++)); do
        for((j=0;j<C;j++)); do
                ADJ="$(adjacentes $i $j P )"
                echo "-${VAR[B,$i,$j]} $ADJ 0"
                ((CLAUSULAS++))
                for XX in $ADJ; do
                        echo "${VAR[B,$i,$j]} -$XX 0"
                        ((CLAUSULAS++))
                done
                ADJ="$(adjacentes $i $j W )"
                echo "-${VAR[S,$i,$j]} $ADJ 0"
                ((CLAUSULAS++))
                for XX in $ADJ; do
                        echo "${VAR[S,$i,$j]} -$XX 0"
                        ((CLAUSULAS++))
                done
        done
done > regradasbrisas

# Escreve as proposições de wumpus no arquivo considerando que inicialmente qualquer posição pode ter um wumpus
MINUMWUMPUS=""
for((i=0;i<L;i++)); do
        for((j=0;j<C;j++)); do
                MINUMWUMPUS+="${VAR[W,$i,$j]} "
        done
done
MINUMWUMPUS+="0"
echo "$MINUMWUMPUS" >> regradasbrisas

# Acresta mais clausulas no arquivo para indicar que existe apenas um Wumpus no mundo
declare -a POSICOES
for((i=0;i<L;i++)); do
        for((j=0;j<C;j++)); do
                POSICOES+=($i,$j)
        done
done
posicaov=0
for P in ${POSICOES[@]}; do
        for((Pl=posicaov+1;Pl<${#POSICOES[@]};Pl++));do
                echo "-${VAR[W,$P]} -${VAR[W,${POSICOES[$Pl]}]} 0"
        done    
        ((posicaov++))
done >> regradasbrisas

# Adiciona mais clausulas para dizer que a posição (0,0) é segura — não tem poço (P) e não tem Wumpus (W)
KBSIZE=1
echo "-${VAR[P,0,0]} 0" > KB
echo "-${VAR[W,0,0]} 0" > KB

#Sensores
# B - para brisa
# G - brilho nao usaremos hoje
# S - cheiro 
# D - grito da morte! nao usaremos
# P - parece, trombou! nao usaremos

# Coloca na base de conhecimentos o que foi passado no terminal
function LERSENSOR()
{
        local l=$1
        local c=$2
        read B S
        [[ "$B" == 1 ]] && echo "${VAR[B,$l,$c]} 0" >> KB
        [[ "$B" == 0 ]] && echo "-${VAR[B,$l,$c]} 0" >> KB
        [[ "$S" == 1 ]] && echo "${VAR[S,$l,$c]} 0" >> KB
        [[ "$S" == 0 ]] && echo "-${VAR[S,$l,$c]} 0" >> KB
        ((KBSIZE++))
}

# Faz a pergunta negando o que queresmo saber e joga no SAT para responder
# return codes 1 - unsafe
#              0 - safe
#              2 - incerto
function pergunta()
{
        set -x
        local alpha="$1"
        local alpha1="$2"
        local op=$3
        local NEG="$((-1*$alpha))"
        local NEG1="$((-1*$alpha1))"
        > pergunta
        if [[ "$op" == "AND" ]]; then
                echo "$NEG $NEG1 0" >> pergunta
        else
                echo "$NEG 0" >> pergunta
                echo "$NEG1 0" >> pergunta
        fi
        cat regradasbrisas KB >> pergunta
        set +x
        echo "p cnf $TOTVARS $((CLAUSULAS+KBSIZE+1))" > pergunta.cnf
        cat pergunta >> pergunta.cnf
        clasp pergunta.cnf
        if (( $? == 20 )); then
        ## XXX: O erro feito em sala era justamente que estava sendo armazenado o contrário
        #na base de conhecimento. Quando invertemos a pergunta, esquecemos de inverter aqui.
        #Agora foi resolvido enviando o alpha do jeito que se espera a pergunta, aqui na função
        #inverte o sinal de alpha para fazer a conjunção, e caso seja UNSAT, armazena na KB
        #o alpha original.
                echo "$alpha 0" >> KB
                echo "$alpha1 0" >> KB
                ((KBSIZE++))
                return 1
        fi
        return 2
}
LERSENSOR 0 0
declare -a FILA
FILA=( 0,1 1,0 )
ifila=0
ffila=1

declare -A VISITADOS
VISITADOS[P,0,0]=1

declare -A NAFILA
function moveto()
{
        local pos=$1
        echo "MOVI PARA $pos"
        VISITADOS[P,$pos]=1
        echo -n "Sensor?"
        LERSENSOR  ${pos%,*} ${pos#*,}
        local ADJ=$(adjacentes ${pos%,*} ${pos#*,})
        local f
        local k
        echo -n "   enfileirando:"
        for f in $ADJ; do
                k="${VAR[r,$f]}"
                [[ -n "${VISITADOS[$k]}" ]] && echo "pulando $f" && continue
                [[ -n "${NAFILA[$k]}" ]] && continue
                ((ffila++))
                FILA[$ffila]="${k#?,}"
                NAFILA[$k]=1
                echo -n " ${k#?,}"
        done
        echo
}

while (( ifila<=ffila )); do
        next=${FILA[$ifila]}
        unset ${FILA[$ifila]}
        unset ${NAFILA[P,$next]}
        ((ifila++))
        echo "-- Decidindo ${VAR[r,${VAR[P,$next]}]}"
        pergunta -${VAR[P,$next]} -${VAR[W,$next]} "AND"
        ret=$?
        (( ret == 0 )) && echo "$next é inseguro! FUJA!"
        (( ret == 1 )) && echo "$next é seguro, bora lá!!!!" && moveto $next
        (( ret == 2 )) && echo "$next é incerto, não vamos arriscar!!!!"
done
