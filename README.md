# VoiceDesk

A small, working AI voice assistant for a business phone line. A caller
talks to a VAPI.ai assistant; VAPI converts speech to text and calls a
FastAPI backend, which classifies the caller's intent with an LLM,
performs a small action (book an appointment, log a callback request,
or just answer a question), and returns a spoken reply. A React
dashboard shows every call, its transcript, and the appointments/
callbacks it produced.

This is deliberately small — four intents, three database tables, one
webhook endpoint. It's meant to be fully explainable in an interview,
not a call-center platform.

```
Caller (phone)
   │  speaks
   ▼
VAPI.ai  ──speech-to-text──▶  VAPI's assistant, configured with
   │                          one Function/Tool ("handleRequest")
   │  calls the function
   ▼
FastAPI  POST /webhook/vapi
   │
   ├─▶ OpenAI (structured JSON output): classify intent + draft reply
   │
   ├─▶ SQLite: log the call, and if it's an appointment/callback with
   │           enough info, save that record too
   │
   └─▶ returns { "result": "<reply text>" }
   ▼
VAPI  ──text-to-speech──▶  spoken back to the caller (over the Twilio
                            trunk connected to the VAPI number)
```

## 1. Voice flow, step by step

1. A caller dials the phone number connected to your VAPI assistant.
2. VAPI answers, streams the caller's speech to its speech-to-text
   engine, and feeds the transcript to the assistant's conversation.
3. The assistant is configured with a single custom **Function**
   (`handleRequest`). Its system prompt tells VAPI's model: "call
   `handleRequest` with the caller's message whenever they ask for
   something — don't try to answer yourself."
4. VAPI calls that function by POSTing to our **Server URL**:
   `POST /webhook/vapi` with `message.type = "function-call"`.
5. FastAPI extracts the caller's message and the running conversation,
   sends both to OpenAI with a strict JSON schema, and gets back:
   `{ intent, name, date, time, phone, reply }`.
6. Based on `intent`, we save a row to `appointments` or `callbacks`
   (only once we have enough slots — otherwise `reply` asks for the
   missing piece and nothing is saved yet), and log the turn to `calls`.
7. We return `{ "result": reply }`. VAPI speaks `reply` back to the
   caller over the call.
8. When the call ends, VAPI sends an `end-of-call-report` event, which
   we also log, so every call shows up in the dashboard even if no
   function was ever triggered (e.g. the caller hung up immediately).

## 2. VAPI integration — manual dashboard setup

VAPI account creation, phone number provisioning, and assistant
configuration happen in VAPI's dashboard — this can't be automated
from code, so here's exactly what to click:

1. Create an account at [dashboard.vapi.ai](https://dashboard.vapi.ai)
   and grab your API key (`VAPI_API_KEY`).
2. **Assistant → Create Assistant.** Give it a name ("VoiceDesk") and
   a system prompt, e.g.:
   > You are the phone assistant for [Business Name]. Greet the
   > caller, then figure out what they need. Whenever they ask to
   > book an appointment, request a callback, ask a general question,
   > or say anything else, call the `handleRequest` function with
   > their exact message. Always speak the `result` the function
   > returns — don't make up your own answer.
3. **Functions → Add Function**, named `handleRequest`, with this
   parameter schema:
   ```json
   {
     "type": "object",
     "properties": {
       "message": { "type": "string", "description": "The caller's message, verbatim" }
     },
     "required": ["message"]
   }
   ```
4. **Server URL**: set it to `https://<your-deployed-backend>/webhook/vapi`
   (for local testing, expose your local server with a tunnel — see
   §7 — and paste that URL here).
5. Copy the assistant's ID into `VAPI_ASSISTANT_ID`.
6. **Phone Numbers → Get a number.** VAPI can hand you a free number
   directly, or you can import a Twilio number (§3).
7. Call the number. That's the whole flow, live.

## 3. Twilio's role

Twilio isn't strictly required — VAPI can provision its own phone
number and handle the call transport itself. Twilio only becomes part
of the picture if you want to **bring your own number**:

1. Buy a phone number in the [Twilio console](https://console.twilio.com)
   and copy your Account SID and Auth Token into `TWILIO_ACCOUNT_SID`
   / `TWILIO_AUTH_TOKEN`.
2. In VAPI's dashboard, **Phone Numbers → Import → Twilio**, and enter
   those same credentials plus the number. VAPI takes over routing the
   call's SIP/media through Twilio — you don't write any Twilio call
   handling code yourself for the core flow.
3. `app/config.py` still loads the Twilio env vars so the backend has
   them available if you extend VoiceDesk to also *send* something via
   Twilio directly later (e.g. an SMS confirmation) — that's out of
   scope for this project on purpose, per the "keep it small" brief.

## 4. FastAPI webhook

`POST /webhook/vapi` is the only endpoint VAPI calls. It branches on
`message.type`:

| type | what we do |
|---|---|
| `function-call` | classify intent, run the matching action, log the call, return `{"result": reply}` |
| `end-of-call-report` | log a summary row so every call appears in the dashboard |
| anything else (`status-update`, `speech-update`, `transcript`, `hang`) | acknowledge with 200 so VAPI doesn't retry; no action needed for a project this size |

See `app/services/vapi_service.py` for the payload-parsing helpers and
`app/routes/webhook.py` for the route itself.

## 5. LLM intent detection

`app/services/llm_service.py` sends the caller's message (plus recent
conversation history, for multi-turn slot-filling like "book an
appointment" → "for when?" → "next Tuesday at 3") to OpenAI's chat
completions API with `response_format: json_schema` and `strict: true`.
This forces the model to return exactly:

```json
{ "intent": "appointment", "name": "...", "date": "...", "time": "...", "phone": "...", "reply": "..." }
```

No regex parsing of free text — the schema is enforced by the API
itself. `app/services/action_service.py` then decides, per intent,
whether enough slots are filled to actually write a database row.

## 6. Database

SQLite via SQLAlchemy, three tables, exactly matching the columns in
the brief (`calls`, `appointments`, `callbacks` — see
`app/database.py`). `init_db()` runs `create_all()` on startup, so
there's no migrations tooling to manage for a project this size.

## 7. Local setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # fill in OPENAI_API_KEY at minimum
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive API docs.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`. It polls the backend every 8 seconds.

### Wiring a real phone call to your local machine

VAPI needs a public URL to reach your webhook. During development,
tunnel your local backend with something like:

```bash
ngrok http 8000
```

and paste the `https://....ngrok-free.app/webhook/vapi` URL into the
assistant's Server URL field in the VAPI dashboard (§2, step 4).

### Testing without a live phone call

You don't need a VAPI account to verify the backend works — you can
POST a `function-call` payload straight at the webhook, the same shape
VAPI would send:

```bash
curl -X POST http://localhost:8000/webhook/vapi \
  -H "Content-Type: application/json" \
  -d '{
        "message": {
          "type": "function-call",
          "call": { "id": "test-call-1", "customer": { "number": "+15551234567" } },
          "functionCall": { "parameters": { "message": "I need to book an appointment for tomorrow at 2pm, my name is Alex" } }
        }
      }'
```

You'll get back `{"result": "..."}`, and the call/appointment will
show up in `GET /calls` and `GET /appointments`, and on the dashboard.

## 8. Environment variables

See `backend/.env.example`. `OPENAI_API_KEY` is the only one required
to test intent detection locally; `VAPI_API_KEY` / `VAPI_ASSISTANT_ID`
/ Twilio credentials are only needed once you wire up a real phone
number.

## 9. What's intentionally not here

No auth on the dashboard or API (add an API key middleware before
deploying anywhere public). No retry/dead-letter queue for failed
webhook calls. No calendar sync. No SMS confirmations. No charts
beyond the four summary numbers. Keeping the scope this tight is what
makes the whole thing explainable end-to-end.

See `INTERVIEW_PREP.md` for a walkthrough of the design decisions in
Q&A form.
