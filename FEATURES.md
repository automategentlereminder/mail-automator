# Gentle Reminder: Core Features & Architecture

This document outlines the core architecture and feature set of the Gentle Reminder Smart Automated Mailer. It is designed to be directly ported to your landing page or promotional materials.

## 🔥 The "Humanizer" Engine

Unlike modern SaaS platforms that broadcast thousands of emails instantaneously through marked third-party SMTP servers, Gentle Reminder operates strictly locally. It acts as a digital pair of hands.

By creating a seamless bridge into your native Windows Microsoft Outlook client via COM architecture (`pywin32`), every email dispatched generates the exact same network footprint as if you had manually typed and sent it yourself.

- **Smart Delays:** Built-in randomized micro-delays (25-45 seconds) between sends guarantee your account doesn't trigger automated spam flags for instantaneous bulk operations.
- **Working Hours Shield:** Configure acceptable "Business Hours" (e.g. 09:00 to 17:00). If you have an active campaign queue running and the clock strikes 5 PM, the Engine will automatically hit "Pause" on the Background Thread without losing your place in line.
- **Weekend Blackout:** Toggle the "Skip Weekends" switch. If it's Saturday, the Humanizer Engine locks down completely. It will sleep silently until Monday morning at 9:00 AM, when it quietly resumes your campaign.

## 🧠 Dynamic Spintax Intelligence

Cold emailing usually results in identical blocks of text being flagged by Microsoft and Google after the 50th delivery. Gentle Reminder negates this completely through our built-in Spintax compiler.

1.  **AI Prompts Included:** We've built an AI Prompt Generator right into the interface. Copy our specialized prompt, drop it into ChatGPT, and it will rewrite your sales copy into Spintax format.
2.  **Word-Level Randomness:** Insert brackets like `{Hello|Hi|Greetings}`. For every single prospect in your queue, the system randomly selects one word. By using Spintax heavily throughout your template, you ensure that every single recipient is getting a cryptographically unique sequence of words, meaning Spam bots can never identify a footprint.
3.  **A/B Variant Round-Robin:** Create 3 entirely different email bodies. Gentle Reminder will dynamically distribute "Variant 1", "Variant 2", and "Variant 3" automatically across your active queue so you can isolate which version generates more replies.

## 📊 Powerful Audience Database

We built a lightweight SQLite data-store that scales elegantly. Say goodbye to messy Excel files scattered across your desktop.

- **Intelligent Ingestion:** Import a CSV containing a thousand leads. Select your target email column. The engine instantly converts every _other_ dynamic column (First Name, Company, City) into a queryable JSON string mapped perfectly to the contact.
- **Data Injection:** In your Spintax templates, simply write `{{CSV:First Name}}` and the engine dynamically unpacks the JSON metadata and injects the targeted company data to personalize the message.
- **Granular Scrubbing:** A built-in Audience Manager table allows you to quickly paginate through a list of thousands securely. Easily select leads who opted out and permanently purge them from a specific Category with a single click. Adding manually typed leads takes seconds via our Smart Dialog box.

## 🚀 The Launch Manager

Designed for mass execution in three clicks.

1.  Select your Master Template.
2.  Check the boxes next to your target Audience Categories (e.g., "Texas Startups", "SaaS CEOs Q3", "Angel Investors").
3.  Hit **Launch**!

The SQL compiler dynamically merges all active targets from your selected categories, builds a persistent Queue in the central database, and spins up the Background Python Worker. You can monitor your active progress bar, pause the execution manually, or let the Humanizer take the wheel. If the application crashes or you shut down your PC, simply restart the worker to pick up exactly where you left off.

## 🎨 Immersive Fluent Interface

Built entirely on PyQt6 and QFluentWidgets, Gentle Reminder feels like a 1st-party Windows 11 application.

- Fluid Sidebar Navigation
- Animated Page Rotations & Micro-interactions
- Beautifully structured Status Flags that tell you instantly if your Campaign is paused dynamically.
- System-respecting Light & Dark mode support built-in natively.
