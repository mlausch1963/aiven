-- Table: public.webservers


CREATE ROLE aiven WITH
  LOGIN
  NOSUPERUSER
  INHERIT
  CREATEDB
  NOCREATEROLE
  NOREPLICATION
  ENCRYPTED PASSWORD 'md52bfe4812be0aa4ddb8751d0bde959117';



-- DROP TABLE public.webservers;

CREATE TABLE public.webservers
(
    url character varying(1024) COLLATE pg_catalog."default",
    tstamp timestamp without time zone,
    match boolean,
    http_status integer,
    nw_status character varying(256) COLLATE pg_catalog."default"
)

TABLESPACE pg_default;

ALTER TABLE public.webservers
    OWNER to aiven;
-- Index: ws

-- DROP INDEX public.ws;

CREATE UNIQUE INDEX ws
    ON public.webservers USING btree
    (tstamp ASC NULLS LAST, url COLLATE pg_catalog."C.utf8" ASC NULLS LAST)
    TABLESPACE pg_default;
