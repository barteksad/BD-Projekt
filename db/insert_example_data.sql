INSERT INTO GRA (nazwa, ilu_graczy, formula_rankingu) VALUES ('Szachy', 2, 'w-l');
INSERT INTO GRA (nazwa, ilu_graczy, formula_rankingu) VALUES ('Warcaby', 2, '3*w-2*l');
INSERT INTO GRA (nazwa, ilu_graczy, formula_rankingu) VALUES ('Go', 2, '2*w-3*l');
INSERT INTO GRA (nazwa, ilu_graczy, formula_rankingu) VALUES ('Brydz', 4, 'w-l');

INSERT INTO TYPY_GRACZY (nazwa) VALUES ('Zwykly');
INSERT INTO GRACZ (nazwa, typ) VALUES ('gracz1', 1);
INSERT INTO GRACZ (nazwa, typ) VALUES ('gracz2', 1);
INSERT INTO ROZGRYWKA (id_gry) VALUES (1);
INSERT INTO UDZIAL (id_rozgrywki, id_gracza, czy_wygral) VALUES (1, 1, 1);
INSERT INTO UDZIAL (id_rozgrywki, id_gracza, czy_wygral) VALUES (1, 2, 0);

COMMIT;
