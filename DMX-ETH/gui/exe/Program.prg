PRG 0


END
;
;======================================================
SUB 2	; HWADV - AVANÇO DA LÂMINA COMANDADO POR HARDWARE
;======================================================
;
;			DEFINIÇÕES:
;			- WP:					LÂMINA RETARDADORA - WAVEPLATE. Possui 16 posições angulares
;										de operação (distanciadas de 22,5 graus).
;			- WPn: 				Parâmetro (int) cujos 16 LSB, um para cada posição de operação
;										da WP, são setados se a respectiva posição estiver habilitada.
;			- ePOS:				posição selecionada da WP (apenas um bit setado).
;			- ICS:				Sistema de controle do instrumento que envia instruções e lê
;										variáveis do motor por meio da Ethernet TCP/IP
;			- ADV:				Nome da entrada DI2 do motor, que comanda o avanço da WP.
;			- DONE:				Nome da saída DO2 do motor, que sinaliza que o avanço foi feito.
;			- STOP:				Flag usado pelo ICS para interromper a execução de HWADV.
;			REGRAS DE OPERAÇÃO (cf. diagrma de seguencia HWADV):
;			1) PREPARAÇÃO:
;				-	ICS move WP para a última posição habilitada
;				- ICS carrega WPn
;				- ICS faz DONE=OFF
;				- ICS faz STOP=OFF
;			2) INICIO DO PROCESSO HWADV:
;				- ICS chama a rotina HWADV (GOSUB 0)
;			3) Loop em HWADV:
;				- Calcula deslocamento para mover WP para a próxima posição habilitada
;				- DONE=OFF
;				- Aguarda ADV=ON, verificando se STOP=ON
;				- Avança WP com o deslocamento já calculado
;				= DONE=ON
;				- Aguarda ADV=OFF, verificando se STOP=ON
;
;VARIAVEIS:
;----------
; V53 = WPn
; V55 = CURRENT ePOS
; V56 = NEXT ePOS
; V59 = NEXT WP index
; V60= NEXT displacement value
; V61= CURRENT WP index, lido pelo ICS
; V62= STOP. Reset by SUB 0. ICS must set it (V62=1) to exit from HWADV routine
; V63 = ENCODER COUNTS PER WP REVOLUTION
; V66 = uSteps para um deslocamento de 22,5 graus, setado em INIT
;
; INICIALIZAÇÃO
; -------------
;
	V62 = 0										; Apaga STOP flag
	V66 = -625							; uSteps de 22,5 graus
	V67 = EO									; Armazena EO e seta INC mode
	INC
	EO = 1										; Habilita driver do motor
; Carrega ePOS atual (V55) com a última posição habilitada
; -----------------------
	V55 = 1										; ePOS atual
	V52 = V61									; WP index atual (deve ser a última posição WP habilitada
	WHILE V52 > 1							; V52 será decrementado da última ePOS até a primeira, exclusive,
		V52 = V52 -1						; assim se V52 iniciar com o valor 1 (WP1), V55 = 1, pois o loope
		V55 = V55 << 1					;	não seria executado. Se V52 iniciar com 2, o loop será executado
	ENDWHILE									; apenas 1 vez e V55 = 2 (x02).
; Calcula próxima ePOS (loop WHILE abaixo)
; --------------------
	WHILE V62 = 0							; Checa término da rotina pelo ICS
		V52 = 0 								; flag do término dos loops WHILE internos
		V60 = 0									; zera o deslocamento
		V56 = V55
		V59 = V61
		; As 3 linhas acima já representam os valores esperados para o caso V55=V53
		IF V55 != V53						; V55=V53 em simulação (V55=V53=0) ou ePOS com apenas 1 posição habilitada
			WHILE V52 = 0
				V60 = V60 + V66
				V56 = V56 << 1			; próximo ePOS
				IF V56 > 65535			; ultrapássou a última posição de trabalho ?
					V56 = 1						; carrega a primeira posição de trabalho
					V59 = 1						; carrega o primeiro WP index
				ELSE
					V59 = V59 + 1
				ENDIF
				;V52 = V53 & V56			; determina se próxima posição está habilitada
				V52 = V53
				V52 = V52 & V56			; determina se próxima posição está habilitada
				DELAY = 1000
			ENDWHILE
		ENDIF
	;	DONE=OFF
		DO2 = 0
	;	Aguarda ADV=ON, verificando se STOP=ON
		V52 = 0
		WHILE V52 = 0
			V72 = DI2							; DI2 = ADV
			IF V72 = 1						; verifica se STOP=ON
				V52 = 1
			ENDIF
		ENDWHILE
		DELAY = 1000
		IF V62 = 0
			; Não foi recebido um STOP do ICS
			;	Avança WP com o deslocamento já calculado
			IF V60 != 0						; V60 = 0 na simulação
				XV60								; GO TO NEXT ePOS. V60 (uSteps)
				WAITX
			ENDIF
			;	DONE=ON
			DO2 = 1								; DONE ON
			V61 = V59							; WP index UPDATE
			V55 = V56							; ePOS UPDATE
			;	Aguarda ADV=OFF, verificando se STOP=ON
			V52 = 1
			WHILE V52 = 1
				V52 = DI2						; DI2 = ADV
				IF V62 = 1					; verifica se STOP=ON
					V52 = 0
				ENDIF
			ENDWHILE
		ENDIF
	ENDWHILE
	EO = V67
ENDSUB



