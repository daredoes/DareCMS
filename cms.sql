PGDMP     :    .                u           cms    9.3.17    9.3.13 -    C           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                       false            D           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                       false            E           1262    16389    cms    DATABASE     u   CREATE DATABASE cms WITH TEMPLATE = template0 ENCODING = 'UTF8' LC_COLLATE = 'en_US.UTF-8' LC_CTYPE = 'en_US.UTF-8';
    DROP DATABASE cms;
             postgres    false                        2615    2200    public    SCHEMA        CREATE SCHEMA public;
    DROP SCHEMA public;
             postgres    false            F           0    0    SCHEMA public    COMMENT     6   COMMENT ON SCHEMA public IS 'standard public schema';
                  postgres    false    6            G           0    0    public    ACL     �   REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;
                  postgres    false    6                        3079    11787    plpgsql 	   EXTENSION     ?   CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;
    DROP EXTENSION plpgsql;
                  false            H           0    0    EXTENSION plpgsql    COMMENT     @   COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';
                       false    1            �            1259    16510    admin_account    TABLE     �   CREATE TABLE admin_account (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    hashed character varying DEFAULT ''::character varying NOT NULL,
    access character varying DEFAULT ''::character varying NOT NULL
);
 !   DROP TABLE public.admin_account;
       public         cms    false    6            �            1259    16430    approved_email    TABLE     ^   CREATE TABLE approved_email (
    id uuid NOT NULL,
    subject character varying NOT NULL
);
 "   DROP TABLE public.approved_email;
       public         cms    false    6            �            1259    16478    contact_item    TABLE     f  CREATE TABLE contact_item (
    id uuid NOT NULL,
    name character varying DEFAULT ''::character varying NOT NULL,
    link character varying DEFAULT ''::character varying NOT NULL,
    description character varying DEFAULT ''::character varying NOT NULL,
    icon character varying DEFAULT 'link'::character varying NOT NULL,
    user_id uuid NOT NULL
);
     DROP TABLE public.contact_item;
       public         cms    false    6            �            1259    16417    email    TABLE     �  CREATE TABLE email (
    id uuid NOT NULL,
    fk_id uuid,
    ident character varying DEFAULT ''::character varying NOT NULL,
    model character varying DEFAULT ''::character varying NOT NULL,
    "when" timestamp without time zone NOT NULL,
    subject character varying DEFAULT ''::character varying NOT NULL,
    dest character varying DEFAULT ''::character varying NOT NULL,
    body character varying DEFAULT ''::character varying NOT NULL
);
    DROP TABLE public.email;
       public         cms    false    6            �            1259    16543    hobby    TABLE     �   CREATE TABLE hobby (
    id uuid NOT NULL,
    name character varying DEFAULT ''::character varying NOT NULL,
    user_id uuid NOT NULL
);
    DROP TABLE public.hobby;
       public         cms    false    6            �            1259    16557    job_experience    TABLE     �  CREATE TABLE job_experience (
    id uuid NOT NULL,
    name character varying DEFAULT ''::character varying NOT NULL,
    link character varying DEFAULT ''::character varying NOT NULL,
    description character varying DEFAULT ''::character varying NOT NULL,
    icon character varying DEFAULT 'link'::character varying NOT NULL,
    user_id uuid NOT NULL,
    start_date date NOT NULL,
    end_date date,
    job_title character varying DEFAULT ''::character varying NOT NULL
);
 "   DROP TABLE public.job_experience;
       public         cms    false    6            �            1259    16495    language    TABLE     �   CREATE TABLE language (
    id uuid NOT NULL,
    name character varying DEFAULT ''::character varying NOT NULL,
    user_id uuid NOT NULL,
    level integer DEFAULT 99 NOT NULL
);
    DROP TABLE public.language;
       public         cms    false    6            �            1259    16527    life_experience    TABLE     >  CREATE TABLE life_experience (
    id uuid NOT NULL,
    name character varying DEFAULT ''::character varying NOT NULL,
    description character varying DEFAULT ''::character varying NOT NULL,
    icon character varying DEFAULT 'link'::character varying NOT NULL,
    user_id uuid NOT NULL,
    date date NOT NULL
);
 #   DROP TABLE public.life_experience;
       public         cms    false    6            �            1259    16575    password_reset    TABLE     �   CREATE TABLE password_reset (
    id uuid NOT NULL,
    account_id uuid NOT NULL,
    generated timestamp without time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
    hashed character varying DEFAULT ''::character varying NOT NULL
);
 "   DROP TABLE public.password_reset;
       public         cms    false    6            �            1259    16463    skill    TABLE     �   CREATE TABLE skill (
    id uuid NOT NULL,
    name character varying DEFAULT ''::character varying NOT NULL,
    user_id uuid NOT NULL,
    level integer DEFAULT 99 NOT NULL
);
    DROP TABLE public.skill;
       public         cms    false    6            �            1259    16404    tracking    TABLE     �  CREATE TABLE tracking (
    id uuid NOT NULL,
    fk_id uuid NOT NULL,
    model character varying DEFAULT ''::character varying NOT NULL,
    "when" timestamp without time zone NOT NULL,
    who character varying DEFAULT ''::character varying NOT NULL,
    which character varying DEFAULT ''::character varying NOT NULL,
    links character varying DEFAULT ''::character varying NOT NULL,
    action integer NOT NULL,
    data character varying DEFAULT ''::character varying NOT NULL
);
    DROP TABLE public.tracking;
       public         cms    false    6            �            1259    16438    user    TABLE     �  CREATE TABLE "user" (
    id uuid NOT NULL,
    watchlist_id uuid,
    verified boolean DEFAULT false NOT NULL,
    first_name character varying DEFAULT ''::character varying NOT NULL,
    last_name character varying DEFAULT ''::character varying NOT NULL,
    email character varying DEFAULT ''::character varying NOT NULL,
    birthdate date,
    no_cellphone boolean DEFAULT false NOT NULL,
    cellphone character varying DEFAULT ''::character varying NOT NULL,
    found_how character varying DEFAULT ''::character varying NOT NULL,
    comments character varying DEFAULT ''::character varying NOT NULL,
    admin_notes character varying DEFAULT ''::character varying NOT NULL,
    about_me character varying DEFAULT 'The rest is still unwritten.'::character varying NOT NULL,
    pic_content_type character varying DEFAULT ''::character varying NOT NULL,
    pic_filename character varying DEFAULT ''::character varying NOT NULL
);
    DROP TABLE public."user";
       public         cms    false    6            �            1259    16390 
   watch_list    TABLE     �  CREATE TABLE watch_list (
    id uuid NOT NULL,
    first_names character varying DEFAULT ''::character varying NOT NULL,
    last_name character varying DEFAULT ''::character varying NOT NULL,
    email character varying DEFAULT ''::character varying NOT NULL,
    birthdate date,
    reason character varying DEFAULT ''::character varying NOT NULL,
    action character varying DEFAULT ''::character varying NOT NULL,
    active boolean DEFAULT true NOT NULL
);
    DROP TABLE public.watch_list;
       public         cms    false    6            �           2606    16519    admin_account_pkey 
   CONSTRAINT     W   ALTER TABLE ONLY admin_account
    ADD CONSTRAINT admin_account_pkey PRIMARY KEY (id);
 J   ALTER TABLE ONLY public.admin_account DROP CONSTRAINT admin_account_pkey;
       public         cms    false    179    179            �           2606    16521    admin_account_user_id_key 
   CONSTRAINT     ^   ALTER TABLE ONLY admin_account
    ADD CONSTRAINT admin_account_user_id_key UNIQUE (user_id);
 Q   ALTER TABLE ONLY public.admin_account DROP CONSTRAINT admin_account_user_id_key;
       public         cms    false    179    179            �           2606    16437    approved_email_pkey 
   CONSTRAINT     Y   ALTER TABLE ONLY approved_email
    ADD CONSTRAINT approved_email_pkey PRIMARY KEY (id);
 L   ALTER TABLE ONLY public.approved_email DROP CONSTRAINT approved_email_pkey;
       public         cms    false    174    174            �           2606    16489    contact_item_pkey 
   CONSTRAINT     U   ALTER TABLE ONLY contact_item
    ADD CONSTRAINT contact_item_pkey PRIMARY KEY (id);
 H   ALTER TABLE ONLY public.contact_item DROP CONSTRAINT contact_item_pkey;
       public         cms    false    177    177            �           2606    16429 
   email_pkey 
   CONSTRAINT     G   ALTER TABLE ONLY email
    ADD CONSTRAINT email_pkey PRIMARY KEY (id);
 :   ALTER TABLE ONLY public.email DROP CONSTRAINT email_pkey;
       public         cms    false    173    173            �           2606    16551 
   hobby_pkey 
   CONSTRAINT     G   ALTER TABLE ONLY hobby
    ADD CONSTRAINT hobby_pkey PRIMARY KEY (id);
 :   ALTER TABLE ONLY public.hobby DROP CONSTRAINT hobby_pkey;
       public         cms    false    181    181            �           2606    16569    job_experience_pkey 
   CONSTRAINT     Y   ALTER TABLE ONLY job_experience
    ADD CONSTRAINT job_experience_pkey PRIMARY KEY (id);
 L   ALTER TABLE ONLY public.job_experience DROP CONSTRAINT job_experience_pkey;
       public         cms    false    182    182            �           2606    16504    language_pkey 
   CONSTRAINT     M   ALTER TABLE ONLY language
    ADD CONSTRAINT language_pkey PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.language DROP CONSTRAINT language_pkey;
       public         cms    false    178    178            �           2606    16537    life_experience_pkey 
   CONSTRAINT     [   ALTER TABLE ONLY life_experience
    ADD CONSTRAINT life_experience_pkey PRIMARY KEY (id);
 N   ALTER TABLE ONLY public.life_experience DROP CONSTRAINT life_experience_pkey;
       public         cms    false    180    180            �           2606    16586    password_reset_account_id_key 
   CONSTRAINT     f   ALTER TABLE ONLY password_reset
    ADD CONSTRAINT password_reset_account_id_key UNIQUE (account_id);
 V   ALTER TABLE ONLY public.password_reset DROP CONSTRAINT password_reset_account_id_key;
       public         cms    false    183    183            �           2606    16584    password_reset_pkey 
   CONSTRAINT     Y   ALTER TABLE ONLY password_reset
    ADD CONSTRAINT password_reset_pkey PRIMARY KEY (id);
 L   ALTER TABLE ONLY public.password_reset DROP CONSTRAINT password_reset_pkey;
       public         cms    false    183    183            �           2606    16472 
   skill_pkey 
   CONSTRAINT     G   ALTER TABLE ONLY skill
    ADD CONSTRAINT skill_pkey PRIMARY KEY (id);
 :   ALTER TABLE ONLY public.skill DROP CONSTRAINT skill_pkey;
       public         cms    false    176    176            �           2606    16416    tracking_pkey 
   CONSTRAINT     M   ALTER TABLE ONLY tracking
    ADD CONSTRAINT tracking_pkey PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.tracking DROP CONSTRAINT tracking_pkey;
       public         cms    false    172    172            �           2606    16457 	   user_pkey 
   CONSTRAINT     G   ALTER TABLE ONLY "user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);
 :   ALTER TABLE ONLY public."user" DROP CONSTRAINT user_pkey;
       public         cms    false    175    175            �           2606    16403    watch_list_pkey 
   CONSTRAINT     Q   ALTER TABLE ONLY watch_list
    ADD CONSTRAINT watch_list_pkey PRIMARY KEY (id);
 D   ALTER TABLE ONLY public.watch_list DROP CONSTRAINT watch_list_pkey;
       public         cms    false    171    171            �           2606    16522    admin_account_user_id_fkey    FK CONSTRAINT     z   ALTER TABLE ONLY admin_account
    ADD CONSTRAINT admin_account_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);
 R   ALTER TABLE ONLY public.admin_account DROP CONSTRAINT admin_account_user_id_fkey;
       public       cms    false    179    175    1976            �           2606    16490    contact_item_user_id_fkey    FK CONSTRAINT     x   ALTER TABLE ONLY contact_item
    ADD CONSTRAINT contact_item_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);
 P   ALTER TABLE ONLY public.contact_item DROP CONSTRAINT contact_item_user_id_fkey;
       public       cms    false    177    1976    175            �           2606    16552    hobby_user_id_fkey    FK CONSTRAINT     j   ALTER TABLE ONLY hobby
    ADD CONSTRAINT hobby_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);
 B   ALTER TABLE ONLY public.hobby DROP CONSTRAINT hobby_user_id_fkey;
       public       cms    false    181    1976    175            �           2606    16570    job_experience_user_id_fkey    FK CONSTRAINT     |   ALTER TABLE ONLY job_experience
    ADD CONSTRAINT job_experience_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);
 T   ALTER TABLE ONLY public.job_experience DROP CONSTRAINT job_experience_user_id_fkey;
       public       cms    false    175    1976    182            �           2606    16505    language_user_id_fkey    FK CONSTRAINT     p   ALTER TABLE ONLY language
    ADD CONSTRAINT language_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);
 H   ALTER TABLE ONLY public.language DROP CONSTRAINT language_user_id_fkey;
       public       cms    false    1976    178    175            �           2606    16538    life_experience_user_id_fkey    FK CONSTRAINT     ~   ALTER TABLE ONLY life_experience
    ADD CONSTRAINT life_experience_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);
 V   ALTER TABLE ONLY public.life_experience DROP CONSTRAINT life_experience_user_id_fkey;
       public       cms    false    180    1976    175            �           2606    16587    password_reset_account_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY password_reset
    ADD CONSTRAINT password_reset_account_id_fkey FOREIGN KEY (account_id) REFERENCES admin_account(id);
 W   ALTER TABLE ONLY public.password_reset DROP CONSTRAINT password_reset_account_id_fkey;
       public       cms    false    179    1984    183            �           2606    16473    skill_user_id_fkey    FK CONSTRAINT     j   ALTER TABLE ONLY skill
    ADD CONSTRAINT skill_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);
 B   ALTER TABLE ONLY public.skill DROP CONSTRAINT skill_user_id_fkey;
       public       cms    false    176    175    1976            �           2606    16458    user_watchlist_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY "user"
    ADD CONSTRAINT user_watchlist_id_fkey FOREIGN KEY (watchlist_id) REFERENCES watch_list(id) ON DELETE SET NULL;
 G   ALTER TABLE ONLY public."user" DROP CONSTRAINT user_watchlist_id_fkey;
       public       cms    false    175    1968    171           