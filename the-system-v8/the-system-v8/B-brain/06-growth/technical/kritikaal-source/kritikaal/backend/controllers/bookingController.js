import { sendEmail } from '../services/emailService.js';
import { saveBooking } from '../utils/storage.js';
import supabase from '../supabaseClient.js';

export const handleBookCall = async (req, res) => {
  console.log('📨 Booking request received:', req.body);
  try {
    const { firstName, lastName, company, country, email, phone, leatherDesign, preferredDate, preferredTime, message } = req.body;

    // Validate required fields
    if (!firstName || !lastName || !company || !country || !email || !phone || !leatherDesign || !preferredDate || !preferredTime) {
      return res.status(400).json({
        success: false,
        message: 'Please fill all mandatory fields (First Name, Last Name, Company, Country, Email, Phone, Leather Design, Date, Time)'
      });
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.status(400).json({
        success: false,
        message: 'Please provide a valid email address'
      });
    }

    // Insert into clients table first
    const { data: newClient, error: clientError } = await supabase
      .from("clients")
      .insert([
        {
          first_name: firstName,
          last_name: lastName,
          email,
          phone: phone || 'Not provided',
          company: company || 'Not provided',
          country: country || 'Not provided',
          leather_design: leatherDesign || 'Not provided',
          source: "Website Booking",
        },
      ])
      .select()
      .single();

    if (clientError) {
      console.error('❌ Supabase client insert error:', clientError.message, clientError.details, clientError.hint);
      // We might not want to fail the whole booking if just the CRM client creation fails
      // So we log and continue, or handle as needed. Here we proceed with booking.
      console.warn("⚠️ Continuing with booking despite client creation failure.");
    } else {
      console.log('✅ Client created/found in Supabase:', newClient?.id);
    }

    // Save notes if provided
    if (message && newClient && newClient.id) {
        const { error: noteError } = await supabase
            .from("notes")
            .insert([{ content: message, client_id: newClient.id }]);
        if (noteError) console.error("Error creating note:", noteError);
    }

    // Prepare booking data
    const bookingData = {
      name: `${firstName} ${lastName}`.trim(),
      firstName,
      lastName,
      company: company || 'Not provided',
      country: country || 'Not provided',
      leatherDesign: leatherDesign || 'Not provided',
      email,
      phone: phone || 'Not provided',
      preferredDate,
      preferredTime: preferredTime || 'Not specified',
      message: message || 'No message provided',
      submittedAt: new Date().toISOString(),
      confirmed: true  // Immediately confirmed
    };

    console.log('📝 New booking request:', bookingData);

    // Save booking to simple file backend. Wrapped in try/catch and tokenized
    try {
      const token = Date.now().toString();
      saveBooking(token, bookingData);
      console.log('💾 Booking saved to storage');
    } catch (storageError) {
      console.warn('⚠️  Failed to save booking:', storageError.message);
    }

    // Send emails concurrently and wait for them to finish
    const userEmailPromise = sendEmail({
      from: "Kritikaal <contact@kritikaal.com>",
      to: bookingData.email,
      subject: "Booking Confirmed",
      html: `
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 800px; margin: 0 auto; background-color: #ffffff; color: #333333;">
  
  <div style="background-color: #1a1a1a; padding: 40px 20px; text-align: center; color: #ffffff;">
    <h1 style="margin: 0 0 10px 0; font-size: 24px; font-weight: 600;">🎉 Thank You for Your Booking!</h1>
    <p style="margin: 0; font-size: 16px; color: #cccccc;">Your consultation has been confirmed</p>
  </div>
  
  <div style="padding: 40px 30px;">
    <p style="font-size: 16px; margin-bottom: 30px;">Dear <strong>${bookingData.name}</strong>,</p>
    
    <div style="background-color: #f0f7ff; border: 1px solid #cce5ff; border-radius: 6px; padding: 25px; text-align: center; margin-bottom: 30px;">
      <h2 style="color: #28a745; margin: 0 0 10px 0; font-size: 20px;">✅ Booking Confirmed!</h2>
      <p style="color: #666666; margin: 0; font-size: 15px;">We've received your booking request and will contact you shortly.</p>
    </div>

    <p style="font-size: 15px; color: #666666; margin-bottom: 40px;">
      Thank you for choosing Kritikaal. We're excited to discuss your custom leather project with you!
    </p>

    <div style="background-color: #fcfcfc; padding: 25px; margin-bottom: 40px;">
      <table style="width: 100%; border-collapse: collapse; font-size: 15px;">
        <tr>
          <td style="padding: 8px 0; color: #666666; width: 140px;">📅 Preferred Date:</td>
          <td style="padding: 8px 0; color: #333333; font-weight: 500;">${bookingData.preferredDate}</td>
        </tr>
        <tr>
          <td style="padding: 8px 0; color: #666666;">⏰ Preferred Time:</td>
          <td style="padding: 8px 0; color: #333333; font-weight: 500;">${bookingData.preferredTime}</td>
        </tr>
        <tr>
          <td style="padding: 8px 0; color: #666666;">📧 Email:</td>
          <td style="padding: 8px 0;"><a href="mailto:${bookingData.email}" style="color: #0066cc; text-decoration: none;">${bookingData.email}</a></td>
        </tr>
        <tr>
          <td style="padding: 8px 0; color: #666666;">📱 Phone:</td>
          <td style="padding: 8px 0; color: #333333;">${bookingData.phone}</td>
        </tr>
        <tr>
          <td style="padding: 8px 0; color: #666666; vertical-align: top;">💬 Your Message:</td>
          <td style="padding: 8px 0; color: #555555;">${bookingData.message}</td>
        </tr>
      </table>
    </div>

    <div style="margin-bottom: 40px;">
      <h3 style="font-size: 16px; margin: 0 0 15px 0;">What happens next?</h3>
      <ul style="color: #666666; font-size: 15px; padding-left: 20px; margin: 0; line-height: 1.6;">
        <li>Our team will review your booking details</li>
        <li>We'll contact you within 24 hours to confirm the appointment</li>
        <li>Get ready to discuss your custom leather vision!</li>
      </ul>
    </div>

    <p style="font-size: 15px; color: #666666; margin-bottom: 0;">
      If you have any questions or need to make changes, please don't hesitate to reach out.
    </p>
  </div>
  
  <div style="text-align: center; padding: 30px; font-size: 13px; color: #999999; border-top: 1px solid #eeeeee;">
    <p style="margin: 0 0 5px 0;"><strong>Kritikaal - Premium Custom Leather Goods</strong></p>
    <p style="margin: 0 0 15px 0;">Making luxury leather accessible from India</p>
    <p style="margin: 0 0 5px 0;">This email was sent because you requested a consultation on our website.</p>
    <p style="margin: 0;">If you didn't make this request, please ignore this email.</p>
  </div>
</div>
      `
    }).then(() => console.log('✅ User email sent successfully'))
      .catch(emailError => console.warn('⚠️  Failed to send user email (async):', emailError.message));

    const adminEmail = process.env.ADMIN_EMAIL || "contact@kritikaal.com";
    const adminEmailPromise = sendEmail({
      from: "contact@kritikaal.com",
      to: adminEmail,
      subject: "New Premium Lead: " + bookingData.name,
      html: `
<div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border: 1px solid #eaeaea;">
  <div style="background-color: #1a1a1a; padding: 20px; text-align: center;">
    <h2 style="color: #ffffff; margin: 0; font-size: 22px;">New Consultation Request 🚀</h2>
  </div>
  
  <div style="padding: 30px;">
    <p style="font-size: 16px; color: #333;"><strong>${bookingData.name}</strong> has just booked a call. Here are the details:</p>
    
    <table style="width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 15px;">
      <tr>
        <td style="padding: 12px; border-bottom: 1px solid #eee; background-color: #f9f9f9; width: 130px;"><strong>Client Name</strong></td>
        <td style="padding: 12px; border-bottom: 1px solid #eee;">${bookingData.name}</td>
      </tr>
      <tr>
        <td style="padding: 12px; border-bottom: 1px solid #eee; background-color: #f9f9f9;"><strong>Date</strong></td>
        <td style="padding: 12px; border-bottom: 1px solid #eee; font-weight: bold; color: #d4af37;">${bookingData.preferredDate}</td>
      </tr>
      <tr>
        <td style="padding: 12px; border-bottom: 1px solid #eee; background-color: #f9f9f9;"><strong>Time</strong></td>
        <td style="padding: 12px; border-bottom: 1px solid #eee; font-weight: bold; color: #d4af37;">${bookingData.preferredTime}</td>
      </tr>
      <tr>
        <td style="padding: 12px; border-bottom: 1px solid #eee; background-color: #f9f9f9;"><strong>Email</strong></td>
        <td style="padding: 12px; border-bottom: 1px solid #eee;">
          <a href="mailto:${bookingData.email}" style="color: #0056b3;">${bookingData.email}</a>
        </td>
      </tr>
      <tr>
        <td style="padding: 12px; border-bottom: 1px solid #eee; background-color: #f9f9f9;"><strong>Phone</strong></td>
        <td style="padding: 12px; border-bottom: 1px solid #eee;">${bookingData.phone}</td>
      </tr>
      <tr>
        <td style="padding: 12px; border-bottom: 1px solid #eee; background-color: #f9f9f9;"><strong>Company</strong></td>
        <td style="padding: 12px; border-bottom: 1px solid #eee;">${bookingData.company}</td>
      </tr>
      <tr>
        <td style="padding: 12px; border-bottom: 1px solid #eee; background-color: #f9f9f9;"><strong>Country</strong></td>
        <td style="padding: 12px; border-bottom: 1px solid #eee;">${bookingData.country}</td>
      </tr>
      <tr>
        <td style="padding: 12px; border-bottom: 1px solid #eee; background-color: #f9f9f9;"><strong>Interest</strong></td>
        <td style="padding: 12px; border-bottom: 1px solid #eee;">${bookingData.leatherDesign}</td>
      </tr>
      <tr>
        <td style="padding: 12px; border-bottom: 1px solid #eee; background-color: #f9f9f9;"><strong>Message</strong></td>
        <td style="padding: 12px; border-bottom: 1px solid #eee; font-style: italic;">"${bookingData.message}"</td>
      </tr>
    </table>
  </div>
</div>
      `
    }).then(() => console.log('✅ Admin notification sent successfully'))
      .catch(emailError => console.warn('⚠️  Failed to send admin notification (async):', emailError.message));

    // Await both promises to ensure they finish before sending response
    await Promise.allSettled([userEmailPromise, adminEmailPromise]);

    // Return success response
    res.status(200).json({
      success: true,
      message: 'Booking submitted successfully! Check your email for confirmation.',
      booking: {
        name: bookingData.name,
        email: bookingData.email,
        preferredDate: bookingData.preferredDate,
        preferredTime: bookingData.preferredTime
      }
    });

  } catch (error) {
    console.error('❌ CRITICAL Booking error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to process booking. Please try again later.',
      error: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
};

