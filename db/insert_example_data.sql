INSERT INTO GRA (nazwa, ilu_graczy) VALUES ('Szachy', 2);
INSERT INTO GRA (nazwa, ilu_graczy) VALUES ('Warcaby', 2);
INSERT INTO GRA (nazwa, ilu_graczy) VALUES ('Go', 2);
INSERT INTO GRA (nazwa, ilu_graczy) VALUES ('Brydz', 4);

INSERT INTO TYPY_GRACZY (nazwa) VALUES ('Zwykly');
INSERT INTO GRACZ (nazwa, typ) VALUES ('gracz1', 1);
INSERT INTO GRACZ (nazwa, typ) VALUES ('gracz2', 1);
INSERT INTO ROZGRYWKA (id_gry) VALUES (1);
INSERT INTO UDZIAL (id_rozgrywki, id_gracza, czy_wygral) VALUES (1, 1, 1);
INSERT INTO UDZIAL (id_rozgrywki, id_gracza, czy_wygral) VALUES (1, 2, 0);

COMMIT;
