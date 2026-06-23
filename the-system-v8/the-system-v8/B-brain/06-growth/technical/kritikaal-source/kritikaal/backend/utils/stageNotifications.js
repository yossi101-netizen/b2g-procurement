export const STAGE_NOTIFICATIONS = {
  'Lead & Call Booking': {
    subject: "Welcome to KRITIKAAL!",
    template: "Hi {firstName}, thanks for reaching out from {company}. We have received your request."
  },
  'Meeting Scheduled': {
    subject: "Your Meeting is Confirmed!",
    template: "Hi {firstName}, your meeting is scheduled. We look forward to speaking with you."
  },
  'Proposal Sent': {
    subject: "Proposal for {company}",
    template: "Hi {firstName}, we have sent you a proposal. Let us know if you have any questions."
  },
  'Contract Signed': {
    subject: "Welcome Aboard!",
    template: "Hi {firstName}, we're excited to start working with {company}!"
  },
  'Closed Won': {
    subject: "Project Kicked Off",
    template: "Hi {firstName}, your project is officially kicked off."
  },
  'Closed Lost': {
    subject: "Thank You",
    template: "Hi {firstName}, thank you for considering us. We hope our paths cross again."
  }
};
