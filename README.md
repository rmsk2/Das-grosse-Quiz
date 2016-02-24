# Einleitung

Das große Quiz ist ein Spiel, bei dem drei Spieler insgesamt 25 Fragen beantworten müssen. Diese Fragen sind in fünf Kategorien eingeteilt. Jede Kategorie hat fünf Fragen. Jeder Frage ist eine der Punktzahlen 20, 40, 60, 80 oder 100 zugeordnet.

Die vorliegende Software ist in zwei Teile (Client und Server) geteilt. Der Server ist für die Darstellung des Spielfelds und für die Anzeige von Fragen und anderen Informationen für die Spieler gedacht. Mit der Clientsoftware wiederum steuert der Spielleiter den Spielverlauf. Die Clientsoftware soll für die Spieler während des Spiels nicht sichtbar sein. Die Ausgabe des Servers dagegen sollte für alle Spieler, z.B. über einen Beamer, zu sehen sein. Die Clientsoftware kann (muß aber z.B. bei Einsatz von mehreren Monitoren nicht) auf einem anderen Rechner laufen. Die Fragen werden in einer XML Datei gespeichert und können durch editieren dieses Files einfach angepasst werden.

Das Große Quiz wurde in Python3 für Linux entwickelt. Einsgesetzt wurde es bisher auf einem Rapberry Pi 2 (Raspbian Wheezy, Server) in Verbindung mit einem Laptop, auf welchem Ubuntu 14.04 LTS installiert war (Client). 

# Abhängigkeiten

Die Clientsoftware verwendet die Library [xmltodict](https://github.com/martinblech/xmltodict) für das Parsen der XML-Datei, welche die Quizfragen enthält. Die Datei xmltodict.py muß daher in den Client-Ordner kopiert werden, damit der Client lauffähig ist. Wenn der Client auf Ubuntu 14.04 LTS eingesetzt wird, dann sollten alle benötigten Pakete bereits standardmäßig vorinstalliert sein. Bei Einsatz des Clients auf Raspbian Wheezy werden die Pakete libgtk-3-dev und python3-gi benötigt, welche mit den Kommandos

    apt-get install libgtk-3-dev
    apt-get install python3-gi
  
installiert werden könnnen.

Der Server ist auf Raspbian Wheezy "Out of the box" ohne die Installation weiterer Pakete lauffähig. Er basiert für die Grafikausgabe auf der Python3-Version von [pygame](http://pygame.org/news.html), welche aber z.B. unter Ubuntu 14.04 LTS und Debian Wheezy nicht über die Standardrepositories zur Verfügung gestellt wird.

# Installation und Konfiguration

ToDo.

# Über den Server

ToDo.

# Über den Client

ToDo.
