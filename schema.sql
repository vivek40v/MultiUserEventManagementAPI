
DROP TABLE IF EXISTS public.users;

CREATE TABLE IF NOT EXISTS public.users
(
    id SERIAL PRIMARY KEY,
    contactnumber VARCHAR(16) NOT NULL,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(50) NOT NULL,
    pwd VARCHAR(256) NOT NULL,
    dob DATE NOT NULL,
    role VARCHAR(15) NOT NULL DEFAULT 'user',
    ipadddress VARCHAR(15) Default Null,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.users
    OWNER TO postgres;

GRANT ALL ON TABLE public.users TO postgres;




CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_timestamp
BEFORE UPDATE ON public.users
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();


