---
name: email-check
description: Search Gmail for specific emails — brand deals, platform notifications,
             collaboration requests, crypto news, payment confirmations. Gmail is already
             connected via MCP. No setup required.
argument-hint: "[search query] e.g. 'sponsorship' or 'from:tiktok.com' or 'subject:partnership' or 'crypto' or 'payment'"
allowed-tools: mcp__0dfa6538-2a18-4494-a497-69c66574ffe2__gmail_search_messages, mcp__0dfa6538-2a18-4494-a497-69c66574ffe2__gmail_read_thread, mcp__0dfa6538-2a18-4494-a497-69c66574ffe2__gmail_read_message
---

# Email Check Skill

Search and read Gmail using $ARGUMENTS as the search query.
Gmail account: shemarpantophlet@gmail.com (connected via MCP).

## How to Execute

1. Use gmail_search_messages with the query from $ARGUMENTS
2. Return a summary of results: sender, subject, date, snippet
3. If asked to read a specific email, use gmail_read_thread with the threadId
4. Flag anything that needs action (brand deals, payments, important notifications)

## Gmail Search Syntax Examples

| Query | Finds |
|-------|-------|
| `sponsorship OR partnership OR collaboration` | Business inquiries |
| `from:tiktok.com OR from:youtube.com` | Platform notifications |
| `subject:payment OR subject:invoice` | Payment-related emails |
| `crypto OR bitcoin OR OPN` | Crypto-related emails |
| `is:unread` | All unread emails |
| `after:2026/03/01` | Emails since March 2026 |
| `has:attachment` | Emails with attachments |

## What to Summarize Per Email
- Sender name + address
- Subject line
- Date received
- Key content (1-2 sentences)
- Action required? (Yes/No + what)

## Key Contacts to Watch
- Any email about brand deals, sponsorships, or paid collaborations
- TikTok/YouTube platform notifications (monetization, strikes, milestones)
- Crypto exchange alerts (Kraken, Revolut, Binance)
- Payment confirmations or invoices
