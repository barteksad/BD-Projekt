ALTER SESSION SET NLS_LANGUAGE = AMERICAN;
ALTER SESSION SET NLS_TERRITORY = AMERICA;

DROP TABLE TYPY_GRACZY cascade constraints;
DROP TABLE GRACZ cascade constraints;
DROP TABLE GRA cascade constraints;
DROP TABLE UDZIAL cascade constraints;
DROP TABLE ROZGRYWKA cascade constraints;
DROP TABLE RUCH cascade constraints;

CREATE TABLE TYPY_GRACZY (
    id NUMBER  GENERATED ALWAYS as IDENTITY(START with 1 INCREMENT by 1),
    nazwa VARCHAR(50) NOT NULL,
    CONSTRAINT TYPY_GRACZY_pk PRIMARY KEY (id)
);

CREATE TABLE GRACZ (
    id NUMBER GENERATED ALWAYS as IDENTITY(START with 1 INCREMENT by 1),
    nazwa VARCHAR(50) NOT NULL,
    typ NUMBER NOT NULL,
    FOREIGN KEY (typ) REFERENCES TYPY_GRACZY(id),
    CONSTRAINT GRACZ_pk PRIMARY KEY (id)
);

CREATE TABLE GRA (
    id NUMBER GENERATED ALWAYS as IDENTITY(START with 1 INCREMENT by 1),
    nazwa VARCHAR(50),
    ilu_graczy NUMBER NOT NULL, --- jakiś trigger na to pewnie
    formula_rankingu VARCHAR(50) NOT NULL,
    CONSTRAINT GRA_pk PRIMARY KEY (id)
);

CREATE TABLE ROZGRYWKA (
    id NUMBER GENERATED ALWAYS as IDENTITY(START with 1 INCREMENT by 1),
    id_gry NUMBER NOT NULL,
    kiedy TIMESTAMP DEFAULT SYSTIMESTAMP,
    FOREIGN KEY (id_gry) REFERENCES GRA(id),
    CONSTRAINT ROZGRYWKA_pk PRIMARY KEY (id)
);

CREATE TABLE UDZIAL (
    id_rozgrywki NUMBER NOT NULL,
    id_gracza NUMBER NOT NULL,
    czy_wygral NUMBER(1) NOT NULL,
    FOREIGN KEY (id_rozgrywki) REFERENCES ROZGRYWKA(id),
    FOREIGN KEY (id_gracza) REFERENCES GRACZ(id),
    CONSTRAINT UDZIAL_pk PRIMARY KEY (id_rozgrywki, id_gracza)
);

CREATE TABLE RUCH (
    id_rozgrywki NUMBER NOT NULL,
    id_gracza NUMBER NOT NULL,
    nr_ruchu NUMBER NOT NULL, /* do ustalenia kolejności ruchów */
    opis_ruchu VARCHAR(50) NOT NULL,
    FOREIGN KEY (id_rozgrywki, id_gracza) REFERENCES UDZIAL(id_rozgrywki, id_gracza),
    CONSTRAINT RUCH_pk PRIMARY KEY (id_rozgrywki, nr_ruchu)
);

COMMIT;