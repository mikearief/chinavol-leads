const express = require('express');
const app = express();
const port = process.env.PORT || 80;
const path = require('path');

// Middleware
app.use(express.static('public'));
app.use('/webhook/stripe', express.raw({type: 'application/json'}));

// Webhook handler
app.post('/webhook/stripe', (req, res) => {
  const sig = req.headers['stripe-signature'];
  const eventJson = req.body.toString('utf8');
  const event = JSON.parse(eventJson);
  
  console.log(`[WEBHOOK] ${new Date().toISOString()} type=${event.type} id=${event.id}`);
  
  // Log to file for persistence
  const fs = require('fs');
  const logLine = JSON.stringify({time: new Date().toISOString(), event: event.type, id: event.id, data: event.data?.object}) + '\n';
  fs.appendFileSync('/app/logs/webhooks.log', logLine);
  
  res.status(200).send({received: true});
});

// Health check
app.get('/health', (req, res) => res.json({ok: true, time: new Date().toISOString()}));

app.listen(port, '0.0.0.0', () => {
  console.log(`ChinaVol server running on 0.0.0.0:${port}`);
});
