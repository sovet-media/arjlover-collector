-- Table: public.arjlover_source

-- DROP TABLE public.arjlover_source;

CREATE TABLE IF NOT EXISTS public.arjlover_source
(
    url text COLLATE pg_catalog."default" NOT NULL,
    title text COLLATE pg_catalog."default",
    size bigint,
    md5 text COLLATE pg_catalog."default",
    linked text[] COLLATE pg_catalog."default",
    http text COLLATE pg_catalog."default",
    torrent text COLLATE pg_catalog."default",
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    category text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT arjlover_source_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE public.arjlover_source
    OWNER to postgres;



-- Table: public.kinopoisk_source

-- DROP TABLE public.kinopoisk_source;

CREATE TABLE IF NOT EXISTS public.kinopoisk_source
(
    film_id integer NOT NULL,
    name_ru text COLLATE pg_catalog."default",
    year integer,
    description text COLLATE pg_catalog."default",
    countries text[] COLLATE pg_catalog."default",
    genres text[] COLLATE pg_catalog."default",
    rating text COLLATE pg_catalog."default",
    rating_vote_count integer,
    poster_url text COLLATE pg_catalog."default",
    ref_id integer,
    name_en text COLLATE pg_catalog."default",
    CONSTRAINT fk_id FOREIGN KEY (ref_id)
        REFERENCES public.arjlover_source (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE public.kinopoisk_source
    OWNER to postgres;



-- Table: public.rating_source

-- DROP TABLE public.rating_source;

CREATE TABLE IF NOT EXISTS public.rating_source
(
    kp double precision,
    kp_votes integer,
    imdb double precision,
    imdb_votes integer,
    ref_id integer NOT NULL,
    CONSTRAINT fk_id FOREIGN KEY (ref_id)
        REFERENCES public.arjlover_source (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE public.rating_source
    OWNER to postgres;
