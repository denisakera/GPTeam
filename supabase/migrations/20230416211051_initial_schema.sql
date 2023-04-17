CREATE extension if not exists "pgcrypto" with schema "extensions";
create extension if not exists "vector" with schema "extensions";

create type "public"."memory_type" as enum ('reflection', 'observation');
create type "public"."event_type" as enum ('non_message', 'message');


CREATE TABLE "public"."Agents" (
    "id" uuid DEFAULT uuid_generate_v4() NOT NULL,
    "full_name" text,
    "bio" text,
    "directives" text[],
    "ordered_plan_ids" uuid[],
    "state" jsonb,
    PRIMARY KEY ("id")
);


create table "public"."Memories" (
    "id" uuid DEFAULT uuid_generate_v4() not null,
    "created_at" timestamp with time zone default now(),
    "agent_id" uuid,
    "type" memory_type,
    "description" text,
    "related_memory_ids" uuid[],
    "embedding" vector(1536),
    "importance" smallint,
    "last_accessed" timestamp with time zone,
    "related_agent_ids" uuid[],
    PRIMARY KEY ("id")
);

create table "public"."Plans" (
    "id" uuid DEFAULT uuid_generate_v4() not null,
    "created_at" timestamp with time zone default now(),
    "agent_id" uuid,
    "description" text,
    "location_id" uuid,
    "max_duration_hrs" real,
    "stop_condition" text,
    "completed_at" timestamp with time zone,
    PRIMARY KEY ("id")
);

create table "public"."Events" (
    "id" uuid DEFAULT uuid_generate_v4() not null,
    "type" event_type,
    "description" text,
    "world" uuid,
    "location" uuid,
    "witnesses" uuid[],
    PRIMARY KEY ("id")
);

create table "public"."Locations" (
    "id" uuid DEFAULT uuid_generate_v4() not null,
    "world_id" uuid,
    "name" text,
    "description" text,
    "channel_id" bigint,
    "allowed_agent_ids" uuid[],
    PRIMARY KEY ("id")
);

create table "public"."Worlds" (
    "id" uuid DEFAULT uuid_generate_v4() not null,
    "name" text,
    PRIMARY KEY ("id")
);
