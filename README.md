# Diary Agent CLI

A local-first, CLI-first, single-agent diary system built around long-term topic memory.

Instead of asking users to manually write long journal entries every day, Diary Agent CLI acts like a lightweight nightly interviewer: it remembers the important topics in a user’s life, asks a few relevant questions, turns short replies into durable memory records, and synthesizes a meaningful diary entry for the day.

---

## Overview

Diary Agent CLI explores a different way to keep a diary.

Most journaling tools still expect the user to do the hardest part: sit down, remember the day, organize thoughts, and write. That works in theory, but in practice it is often too cognitively expensive to sustain.

This project takes a different approach:

- the user does **not** need to write a full journal entry
- the agent asks **4–5 lightweight questions**
- the system remembers **long-term life topics**
- the interaction updates **topic history and recent status**
- the system generates a **daily diary entry** from the session

The goal is to reduce the cognitive burden of journaling while preserving memory, continuity, and reflection over time.

---

## Product Idea

Diary Agent CLI is **not** a generic chatbot.

It is a structured but warm diary agent designed around three core ideas.

### 1. Topic-centered memory

The system does not treat raw messages as the main unit of memory.

Instead, it models a user’s life as a set of long-lived topics, such as:

- sleep
- fitness
- basketball
- study
- job search
- a short-term group project

Each topic can carry:

- a title
- a long-term description
- a recent status summary
- a lifecycle state such as active, dormant, or archived
- a history of meaningful updates over time

This makes the system more like a personal memory structure than a simple transcript log.

### 2. Lightweight daily interview

Each session is meant to feel light.

The agent:

- selects a few relevant topics for the day
- asks short, natural questions
- may ask one follow-up if needed
- asks one final free-share question near the end

The user can respond naturally and briefly. The system handles the structure.

### 3. Diary synthesis with continuity

The system converts the interaction into:

- topic-level memory records
- updated topic summaries
- a structured diary entry for the day

This means the diary is not just a copy of the chat transcript. It becomes a cleaner and more meaningful personal record.

---

## Why this project exists

Writing a diary is valuable, but it is also tiring.

Many people do not stop journaling because they do not care. They stop because the process asks for too much structure, too much energy, and too much consistency at the wrong moment of the day.

This project is an attempt to make journaling easier by shifting some of the burden from the user to the agent.

The user brings short answers.  
The system brings:

- continuity
- memory structure
- topic tracking
- diary generation

---

## Core Concepts

### Topic

A long-lived life memory unit.

Examples:

- Fitness
- Basketball
- Sleep
- Linear Algebra
- Internship Search

A topic stores both long-term identity and recent state.

### Topic History Item

A durable, topic-level memory record.

This is not just the user’s raw reply. It is a more formal record of what happened for that topic on a given day.

### Daily Session

The orchestration container for one day’s interaction.

It tracks:

- which topics were selected
- which topic is currently being discussed
- what has already been asked
- whether the session was interrupted or resumed
- when the final diary should be generated

### Diary Entry

The final synthesized daily record generated from a session.

---

## Architecture

This project is intentionally designed as:

- **single-agent**
- **explicit orchestration**
- **local-first**
- **CLI-first**
- **deterministic-first**

It does **not** use a multi-agent architecture.  
It does **not** depend on a web UI for the MVP.  
It does **not** hide core behavior behind opaque prompt logic.

The current architecture is an inspectable pipeline:

- **Session Planner** → selects today’s topics
- **Question Composer** → generates lightweight questions
- **Signal Extractor** → turns replies into structured signals
- **Memory Writer** → updates topic memory and history
- **Diary Synthesizer** → creates the day’s diary entry
- **Conversation Orchestrator** → runs the session as an explicit state machine

---

## What the MVP already does

The current CLI MVP already supports:

- local SQLite persistence
- topic lifecycle management
- layered topic selection for each daily session
- lightweight question generation
- deterministic signal extraction
- durable topic history writing
- resumable daily sessions
- diary generation from the current session
- CLI commands for setup, topic inspection, session running, and diary viewing
- automated tests for planner behavior, memory writing, orchestration flow, and resumability

---

## Quick Start

### Requirements

- Python 3.11+
- Git
- recommended: virtual environment

