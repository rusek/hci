HCI
===


Wymagane biblioteki
===

* `bottle`
* `cherrypy`


Środowisko do pracy z płytką
===

Ze strony Intela pobieramy [Arduino IDE](https://communities.intel.com/docs/DOC-22226) i wypakowujemy w
dowolnym miejscu.

Podłączamy płytkę do komputera. Po pewnym czasie powinien pojawić się plik `/dev/ttyACM0` -
w razie problemów można obejrzeć `dmesg | tail`. Płytka przedstawia się jako coś na kształt modemu, więc musimy
grzecznie poprosić menedżera modemów, aby się nią nie bawił: `sudo apt-get remove modemmanager`. Sprawdzamy, do
jakiej grupy przypisane jest urządzenie (`ls -al /dev/ttyACM`, u mnie to `dialout`) i przypisujemy siebie
do tej grupy (`sudo usermod -a -G dialout username`). Upewniamy się, że zmiany uprawnień weszły w życie
(`sudo killall Xorg`, choć może wystarczy się normalnie wylogować; alternatywnie można po prostu zrestartować system).

Po zakończeniu konfiguracji uruchamiamy IDE, ustawiamy port szeregowy i wgrywamy przykład Blink. Uważnie patrzymy na
log z wgrywania: IDE wypisuje sukces, nawet jak próbuje komunikować się poprzez nieistniejący plik urządzenia.
Możemy również oberwać błędem TIMEOUT (opisany w sekcji Known Issues w jednym z poradników Intela do Galileo). Wtedy
restartujemy płytkę. Do restartu służą dwa przyciski: jeden restartuje wyłącznie aktualny szkic (wg mnie nie działa,
ale może się nie znam), drugi zaś całą płytkę (na pewien czas gaśnie dioda USB).


Komunikacja z płytką
===

Komunikację można przetetować wgrywając `cardreader_stub/` na płytkę i otwierając monitor portu szeregowego. By
sprawdzić komunikację pomiędzy płytką a zewnętrznym programem zamykamy monitor portu i odpalamy `./agent.py`.
Skrypt na samym początku powinien odpowiednio skonfigurować urządzenie, a potem czytać kolejne linie.

Płytka powinna wysyłać kolejne komunikaty tekstowo w liniach zakończonych znakami `\r\n`. Komunikat nie powinien
zawierać znaków spoza ASCII - wspomniana już wcześniej sekcja Known Issues w poradniku Intela informuje, że może
to powodować niepoprawne funkcjonowanie płytki. Pewnie lepiej też unikać znaków kontrolnych ASCII.


Komunikacja bez płytki
===

Na potrzeby testowania `./agent.py` może komunikować się z innym procesem zamiast Galileo. W tym celu uruchamiamy
`./agent.py --fakedev`, zaś w innym terminalu `./fakedev.py`. Jeśli zrobimy to w odwrotnej kolejności, to `fakedev.py`
będzie wisieć do czasu wystartowania `agent.py`, ale poza tym nie ma problemów. Komunikacja odbywa się po nazwanym
PIPE-ie. `fakedev.py` oczekuje na polecenia od użytkownika - na razie działa `quit` i `send <data>`, ale jak już
będzie jakiś protokół komunikacji płytka-agent, to pewnie dopisze się wygodniejsze polecenia.


Serwer HTTP
===

W momencie uruchamiania `./agent.py` startowany jest serwer HTTP nasłuchujący na porcie 8080. Na stronie
<http://localhost:8080/static/> powinien zostać wyświetlony ostatni przesłany komunikat.
