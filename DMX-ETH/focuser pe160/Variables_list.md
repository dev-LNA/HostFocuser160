### Variáveis gravadas em RAM

V1: Usado de forma genérica nas funções

V2: Genérico

V3: Genérico

V4: GFOC INIT done flag

V5: Genérico

V6: Genérico

V7: Genérico

V8: Usado dentro das funções para verificar se motor está em movimento

V9: Usado no FOCUS GOTO como uma flag de 'isMoving' #TODO: Verificar essa 
lógica

V10: Usado dentro das funções para 
armazenar valor de encoder convertido para unidade de passos

V11: Usado nas funções para armazenar o estado de MSTX

V12: Usado em FOCUS INIT para armazenar a posição atual

V13: Usado no HOME para indicar quando um comando de parada for solicitado durante o homing, para que, no caso do comando HOME + PARK o park não seja executado

V14: _Não utilizado_

V15: Indica que a função HOME está sendo executada

V16: Indica que o PARK está sendo executado

V17: _Não utilizado_

V18: _Não utilizado_

V19: _Não utilizado_

V20: Armazena a posição de destino solicitada para o comando GOTO

V21: Usado nas funções FOCUS IN e FOCUS OUT para armazenar a velocidade do movimento (recebida no comando do servidor)

V22: _Não utilizado_

V23: Usado para armazenar a posição atual do motor para a checagem de STALL

V24: Usado para armazenar a variação da posição do motor para a checagem de STALL

V25: Flag que indica que foi detectado STALL

V26: _Não utilizado_

V27: _Não utilizado_

V28: _Não utilizado_

V29: _Não utilizado_

V30: Armazena o status obtido pela função STATUS REQUEST (track, index, eo, init, status, latch, io)

V31: Genérico somente na função STATUS REQUEST

V32: #TODO: Tentar entender para que está sendo usado em STATUS REQUEST 

V33: Versão atual do firmware (somente data da versão)

V34: _Não utilizado_

V35: _Não utilizado_

V36: _Não utilizado_

V37: _Não utilizado_

V38: _Não utilizado_

V39: _Não utilizado_

V40: _Não utilizado_

V41: _Não utilizado_ 

V42: Flag de parada de movimento em todas as funções, realiza o comando HALT enviado pelo servidor

V43: _Não utilizado_

V44: Indica que a inicialização foi realizada (Homing feito com sucesso)

V45: _Não utilizado_

V46: Indica que alguma função está em execução no firmware do motor

V47:  _Não utilizado_

V48:  _Não utilizado_

V49:  Em PRG 0 diz que usa para alguma coisa, mas na verdade é  _Não utilizado_

## Variáveis gravadas em FLASH

V50: ID do motor

V51:  _Não utilizado_

V52:  _Não utilizado_ 

V53:  _Não utilizado_

V54:  _Não utilizado_ 

V55:  _Não utilizado_ 

V56:  _Não utilizado_ 

V57:  _Não utilizado_ 

V58:  _Não utilizado_ 

V59:  _Não utilizado_

V60:  _Não utilizado_

V61:  _Não utilizado_

V62:  _Não utilizado_ 

V63:  _Não utilizado_

V64:  _Não utilizado_ 

V65:  _Não utilizado_ 

V66:  _Não utilizado_ 

V67:  _Não utilizado_ 

V68:  _Não utilizado_ 

V69:  _Não utilizado_

V70:  _Não utilizado_

V71:  Posição máxima em unidades do encoder (Inicializado em PRG0)

V72:  _Não utilizado_  

V73:  _Não utilizado_

V74:  Overtravel para eliminar o backlash (Inicializado em PRG0) #TODO Checar a relação disso com a configuração do backlash na aplicação  

V75:  Configuração de HSPD 

V76:  Configuração de LSPD

V77:  _Não utilizado_ 

V78:  _Não utilizado_ 

V79:  _Não utilizado_

V80:  _Não utilizado_

V81:  _Não utilizado_

V82:  _Não utilizado_ 

V83:  Configuração de posição de PARK

V84:  _Não utilizado_ 

V85:  _Não utilizado_ 

V86:  _Não utilizado_ 

V87:  _Não utilizado_ 

V88:  _Não utilizado_ 

V89:  _Não utilizado_

V90:  Firmware version -> Version number

V91:  Firmware version -> Update number

V92:  Firmware version -> Bug fix number 

V93:  _Não utilizado_

V94:  _Não utilizado_ 

V95:  _Não utilizado_ 

V96:  _Não utilizado_ 

V97:  _Não utilizado_ 

V98:  _Não utilizado_ 

V99:  _Não utilizado_

V100:  _Não utilizado_ 