# Einleitung

Das große Quiz ist ein Spiel, bei dem bis zu drei Spieler insgesamt 25 Fragen beantworten müssen. Diese Fragen sind in fünf Kategorien eingeteilt. Jede Kategorie hat fünf Fragen. Jeder Frage ist eine der Punktzahlen 20, 40, 60, 80 oder 100 zugeordnet.

Die vorliegende Software ist in zwei Teile (Client und Server) geteilt. Der Server ist für die Darstellung des Spielfelds und für die Anzeige von Fragen und anderen Informationen für die Spieler gedacht. Mit der Clientsoftware wiederum steuert der Spielleiter den Spielverlauf. Die Clientsoftware soll für die Spieler während des Spiels nicht sichtbar sein. Die Ausgabe des Servers muß dagegen für alle Spieler, z.B. über einen Beamer, zu sehen sein. Die Clientsoftware kann (muß aber z.B. bei Einsatz von mehreren Monitoren nicht) auf einem anderen Rechner laufen. Die Fragen werden in einer XML Datei gespeichert und können durch editieren dieses Files einfach angepasst werden.

Das Große Quiz wurde in Python3 für Linux entwickelt. Einsgesetzt wurde es bisher auf einem Rapberry Pi 2 (Raspbian Wheezy, Server) in Verbindung mit einem Laptop, auf welchem Ubuntu 14.04 LTS installiert war (Client). 

# Abhängigkeiten

Die Clientsoftware verwendet die Library [xmltodict](https://github.com/martinblech/xmltodict) für das Parsen der XML-Datei, welche die Quizfragen enthält. Die Datei xmltodict.py muß daher in den Client-Ordner kopiert oder global installiert werden, damit der Client lauffähig ist. Wenn der Client auf Ubuntu 14.04 LTS eingesetzt wird, dann sollten bis auf xmltodict alle benötigten Pakete bereits standardmäßig vorinstalliert sein. Bei Einsatz des Clients auf Raspbian Wheezy werden darüber hinaus die Pakete libgtk-3-dev und python3-gi benötigt, welche mit den Kommandos

    apt-get install libgtk-3-dev
    apt-get install python3-gi
  
installiert werden könnnen.

Der Server ist auf Raspbian Wheezy "Out of the box" ohne die Installation weiterer Pakete lauffähig. Er basiert für die Grafikausgabe auf der Python3-Version von [pygame](http://pygame.org/news.html), welche aber z.B. unter Ubuntu 14.04 LTS und Debian Wheezy nicht über die Standardrepositories zur Verfügung gestellt wird.

# Installation und Konfiguration

Die Installation des Servers ist simpel: einfach das "server" Verzeichnis auf die Zielmaschine kopieren. Die Installation des
Clients ist nicht wesentlich schwieriger. Dort muß nach Kopieren des "client" Verzeichnisses zusätzlich der Hostname/die IP-Adresse sowie der Port, auf dem der Serverprozess hört, in die Datei questions.xml eingetragen werden. Dafür ist der Tag configuration vorgesehen:

    <configuration>
        <displayserverhost>10.0.1.106</displayserverhost>
        <displayserverport>4321</displayserverport>
    </configuration>

Schöner wäre es natürlich wenn diese Konfigurationsarbeiten direkt über die Clientsoftware durchgeführt werden könnten. Dieses Feature ist bis jetzt allerdings noch nicht implementiert.

# Über den Server

Der Server läßt sich mittels des Kommandos

    python3 displayserver.py

starten. Die Größe des durch den Server angezeigten Fensters ist auf 1024x768 Bildpunkte voreingestellt. Dies kann durch anpassen der Werte der Variablen

    PLAYING_FIELD_X = 1024
    PLAYING_FIELD_Y = 768

aber einfach geändert werden. Die verwendete Schriftgröße bei der Ausgabe von Text wird aus diesen Angaben abgeleitet.

# Über den Client

Die Clientsoftware kann nur dann erfolgreich ausgeführt werden, wenn der Server bereits läuft. Der Client wird dann durch den Befehl

    python3 dgqcontrol.py
    
gestartet.

# Über die XML-"Fragendatei"

Im "client" Verzeichnis muß sich die Datei questions.xml befinden, welche zusätzlich zu den oben bereits erwähnten Daten zur Netzwerkkonfiguration die Namen der Spieler (bzw. Teams) und die zu beantwortenden Fragen enthält. Die Namen der Teams sind unter dem Tag "teams" hinterlegt

    <teams>
        <team>A</team>            
        <team>B</team>            
        <team>C</team>            
    </teams>

und können dort auch verändert werden. Die Anzahl der Teams muss derzeit exakt drei betragen. 

Zu jedem Quiz gehören natürlich auch Quizfragen. Diese sind in questions.xml unter dem Tag questions gespeichert und werden dort nach Kategorien gruppiert:

    <questions>
    
        <qcategory name="Eins">
            <question hastime="True" timeallowance="60" value="20">
                <text>Frage#20</text>
            </question>
            <question hastime="True" timeallowance="60" value="40">
                <text>Frage#40</text>
            </question>
            <question hastime="True" timeallowance="60" value="60">
                <text>Frage#60</text>
            </question>
            <question hastime="True" timeallowance="60" value="80">
                <text>Frage#80</text>
            </question>            
            <question hastime="True" timeallowance="60" value="100">
                <text>Frage#100</text>
            </question>            
        </qcategory>
    .
    .
    .
    </questions>
    
Es müssen genau fünf Kategorien mit jeweils fünf Fragen (mit den Wertigkeiten 20, 40, 60, 80 und 100 Punkte) angegeben werden. Das "name" Attribut der durch den Tag "qcategory" definierten Kategorie legt dabei deren Namen fest. Dieser wird in der Clientsoftware sowie auf dem Spielfeld angezeigt. Eine einzelne Frage wird durch den Tag "question" beschrieben.

    <question hastime="True" timeallowance="60" value="40">
        <text>Frage#40</text>
    </question>
    
Wenn das Attribut "hastime" den Wert "True" aufweist, wird bei der Anzeige der Frage ein Zähler eingeblendet, welcher vom unter dem Attribut "timeallowance" angegebenen Wert auf 0 heruntergezählt wird. Wenn "hastime" nicht "True" ist, dann wird die Frage ohne Zähler dargestellt. Das Attribut "value" determiniert die Wertigkeit der Frage. Der Text der Frage wird durch den Tag "text" festegelegt. Eine besondere Bedeutung kommt dabei dem Zeichen "#" zu: Es steht für einen Zeilenumbruch. Alle Zeilen der Frage werden durch den Server zentriert auf dem Bildschirm ausgegeben.  
