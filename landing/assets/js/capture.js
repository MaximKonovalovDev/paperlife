/* PaperLife wedge form — email capture for the free emergency contact card.

   The form posts to FORM_ENDPOINT. Until the studio's capture service is
   wired (surf-studio / deploy lane), FORM_ENDPOINT is the documented
   placeholder below. The form never pretends the email was captured:
   if the endpoint is unreachable, it falls back to the visitor's mail
   client (GigDeduct honest pattern) and says so on the page.

   Payload: JSON { email, product: "emergency-contact-card", company: "" }
   (company is a honeypot — must be empty).
*/
(function () {
  "use strict";

  // DEPLOY SEAM: point this at the studio capture endpoint, or a form
  // service endpoint that accepts a JSON POST with {email}. The relative
  // stub below 404s until wired — the form then falls back to mailto and
  // says so on the page (it never posts to a placeholder domain).
  // See landing/forms/README.md for the full contract.
  var FORM_ENDPOINT = "forms/submit";
  var MAILTO = "studio@example.com"; // placeholder until the studio inbox is wired

  var form = document.getElementById("capture");
  if (!form) return;

  var note = document.getElementById("form-note");

  function say(text, ok) {
    note.textContent = text;
    note.className = "form-note " + (ok ? "ok" : "err");
  }

  function mailtoFallback(email) {
    var subject = encodeURIComponent("PaperLife: free emergency contact card");
    var body = encodeURIComponent(
      "Please send me the free one-page emergency contact card PDF.\n\nMy email: " + email +
      "\n\n(Capture service not wired yet — sending by hand.)"
    );
    window.location.href = "mailto:" + MAILTO + "?subject=" + subject + "&body=" + body;
    say("The capture service is not wired yet — if your mail app just opened, send the draft and you're in. You can also email us directly at " + MAILTO + ".", false);
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    var email = form.email.value.trim();
    var honeypot = form.company.value.trim();
    if (!email || email.indexOf("@") < 1) {
      say("Please enter a valid email address.", false);
      return;
    }
    if (honeypot) return; // bot

    say("Sending\u2026", true);
    var sent = false;
    fetch(FORM_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: email,
        product: form.product.value,
        company: honeypot
      })
    }).then(function (res) {
      if (!res.ok) throw new Error("HTTP " + res.status);
      sent = true;
      say("On its way \u2014 check your inbox for the free card.", true);
      form.email.value = "";
    }).catch(function () {
      mailtoFallback(email);
    });
  });
})();
