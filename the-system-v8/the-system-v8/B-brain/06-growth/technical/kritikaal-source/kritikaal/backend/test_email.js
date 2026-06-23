import { sendEmail } from './services/emailService.js';

async function test() {
  try {
    const res = await sendEmail({
      to: 'test@example.com',
      subject: 'Test Email',
      html: '<p>Test</p>'
    });
    console.log('Success:', res);
  } catch (err) {
    console.error('Failed:', err);
  }
}

test();
