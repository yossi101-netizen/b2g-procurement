import { sendEmail } from './services/emailService.js';

async function test() {
  try {
    const res1 = await sendEmail({
      to: 'contact@kritikaal.com',
      subject: 'Test Admin Email',
      html: '<p>Test Admin Email</p>'
    });
    console.log('Admin Success:', res1);

    const res2 = await sendEmail({
      to: 'testuser@gmail.com',
      subject: 'Test User Email',
      html: '<p>Test User Email</p>'
    });
    console.log('User Success:', res2);
  } catch (err) {
    console.error('Failed:', err.message);
  }
}

test();
