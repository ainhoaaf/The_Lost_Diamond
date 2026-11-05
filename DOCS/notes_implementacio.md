# Python

- Regles del joc ja es poden fer
- Digital twin ja es pot fer, ja es pot simular una mica sense la part física, després s'adapta a lo que es faci físic
- Publicar el que s'hagi de publicar a MQTT
- deshabilitar fitxes abans i despres del diamant
- Logistica qui te el diamant
- Enviar peces: pirata, pirata desactivat...
- Doble tir
- Si una casella ja ha estat descoberta shi pot caure igual: podem mantenir les dolentes (pirates i naufragi)

# Arduino

- Els meeples poden enviar les dades al codi (subscriptors).
- Meeple només llegeix i envia; si posem led ha de rebre informació.
- Base:
  - enviar quan apreta el botó
  - fer confirmacions de cada cosa que demana que fem el codi (py diu reprodueix musica - io confirma que la fa sonar)
  - tenir 1 funció x cada tipus de peça que pot sortir
  - fer diferents missatges x saber que esta fallant
  - quan ja ha sortir el diamant ho guardem en una variable io
  - Que el que tingui el diamant faci pampallugues

# Normes

Durant el bucle de mirar quants "passos" queden mirar is es pot canviar d'illa. Es a dir, es obligatori treure X número x canviar de illa, pero no cal que el treguis al principi de la jugada.

1. meeple necessita info x saber que es el seu torn i posar-se en verd
2. jugador apreta boto
3. base diu boto apretat
4. python rep boto i diu quin numero treu el dau
5. esp32 agafa numero dau
6. esp32 posara x pantalla
7. meeple es moura, llegirà i enviarà
   1. si està en una casella incorrecta o es moviment il·legal -> python avisa a la pantalla i avisa al meeple de pampallugues vermell
   2. si es casella incorrecta posar musica de error
8. intentar no enviar constantment el uuid, nomes enviar quan canvia
   1. no pots tirar i quedar-te a la mateixa casella
   2. si el meeple esta mes de 15 segons en la mateixa casella enviar un avis
9. quan comptador dau esta a 0, python revela quina casella es
   1. revelar string o numero
   2. la fitxa s'ha de diferenciar quan estan activades, desactivades
   3. que io vegui si ha sortit diamant o no i veure is les fitxes estan activades o desactivades
10. io fer una funcio x cada peça
