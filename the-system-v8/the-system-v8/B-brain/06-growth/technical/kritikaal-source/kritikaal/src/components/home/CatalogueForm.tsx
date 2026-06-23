"use client";

import { motion } from "framer-motion";
import { useTranslation } from "@/contexts/TranslationContext";
import { FileText, Download } from "lucide-react";
import { useEffect, useRef } from "react";
import intlTelInput from "intl-tel-input";
import "intl-tel-input/build/css/intlTelInput.css";

// Import leather design images
import bagImage1 from "@/assets/Calculator/structured-tote-bag.jpeg";
import travelBagImage from "@/assets/Calculator/leather-travel-duffel.png";
import walletImage1 from "@/assets/Calculator/classic-mens-wallet.webp";
import beltImage1 from "@/assets/Calculator/leather-belt.jpeg";

// Extend Window interface for Zoho validation functions
declare global {
  interface Window {
    validateEmail1224645000000593044: () => boolean;
    checkMandatory1224645000000593044: () => boolean;
  }
}

export const CatalogueForm = () => {
  const { t } = useTranslation();
  const phoneInputRef = useRef<HTMLInputElement>(null);
  const itiRef = useRef<any>(null);

  // Load Zoho validation scripts
  useEffect(() => {
    console.log('🔧 CatalogueForm mounted - Loading Zoho scripts...');
    
    // Add validation functions to window
    const script = document.createElement('script');
    script.innerHTML = `
      window.validateEmail1224645000000593044 = function() {
        var form = document.forms['WebToLeads1224645000000593044'];
        var emailFld = form.querySelectorAll('[ftype=email]');
        var i;
        for (i = 0; i < emailFld.length; i++) {
          var emailVal = emailFld[i].value;
          if ((emailVal.replace(/^\\s+|\\s+$/g, '')).length != 0) {
            var atpos = emailVal.indexOf('@');
            var dotpos = emailVal.lastIndexOf('.');
            if (atpos < 1 || dotpos < atpos + 2 || dotpos + 2 >= emailVal.length) {
              alert('Please enter a valid email address.');
              emailFld[i].focus();
              return false;
            }
          }
        }
        return true;
      };

      window.checkMandatory1224645000000593044 = function() {
        console.log('🔍 Zoho validation function called');
        var mndFileds = new Array('Company', 'Last Name', 'Designation', 'Email', 'Phone');
        var fldLangVal = new Array('Company', 'Name', 'Design Type', 'Email', 'Phone');
        for (i = 0; i < mndFileds.length; i++) {
          var fieldObj = document.forms['WebToLeads1224645000000593044'][mndFileds[i]];
          if (fieldObj) {
            if (((fieldObj.value).replace(/^\\s+|\\s+$/g, '')).length == 0) {
              if (fieldObj.type == 'file') {
                alert('Please select a file to upload.');
                fieldObj.focus();
                return false;
              }
              alert(fldLangVal[i] + ' cannot be empty.');
              fieldObj.focus();
              return false;
            } else if (fieldObj.nodeName == 'SELECT') {
              if (fieldObj.options[fieldObj.selectedIndex].value == '-None-') {
                alert(fldLangVal[i] + ' cannot be none.');
                fieldObj.focus();
                return false;
              }
            } else if (fieldObj.type == 'checkbox') {
              if (fieldObj.checked == false) {
                alert('Please accept ' + fldLangVal[i]);
                fieldObj.focus();
                return false;
              }
            }
            try {
              if (fieldObj.name == 'Last Name') {
                name = fieldObj.value;
              }
            } catch (e) {}
          }
        }
        if (!window.validateEmail1224645000000593044()) {
          return false;
        }
        var urlparams = new URLSearchParams(window.location.search);
        if (urlparams.has('service') && (urlparams.get('service') === 'smarturl')) {
          var webform = document.getElementById('webform1224645000000593044');
          var service = urlparams.get('service');
          var smarturlfield = document.createElement('input');
          smarturlfield.setAttribute('type', 'hidden');
          smarturlfield.setAttribute('value', service);
          smarturlfield.setAttribute('name', 'service');
          webform.appendChild(smarturlfield);
        }
        var submitBtn = document.querySelector('.crmWebToEntityForm .formsubmit');
        if (submitBtn) {
          submitBtn.setAttribute('disabled', 'true');
        }
        console.log('✅ Zoho validation passed');
        return true;
      };
      
      console.log('✅ Zoho validation functions loaded');
    `;
    document.head.appendChild(script);

    // Add analytics script
    const analyticsScript = document.createElement('script');
    analyticsScript.id = 'wf_anal';
    analyticsScript.src = 'https://crm.zohopublic.in/crm/WebFormAnalyticsServeServlet?rid=193218012c5131a752f0645fd7ffa90ccc2ed673982f67d5a8ea158a318602a063230e10e0a21c77494ac69912e5660dgidb6e85b469b34037c9f18043ab3448fbf8830c1705f586c06e1530c5f5b01276fgid2e6120e10c1436812a9deb60b20b1a0b8901033e4072e3c0eb893d8305d480c3gid76cb4a980b6f4350d4152e120406f3ca0b9e7dff53a934a6a847c3702975fd27&tw=b3603a39e884023d72b9cbb732179e09a022e8e110eae3c468ec761d1875cd7d';
    document.head.appendChild(analyticsScript);
    
    console.log('✅ Zoho analytics script loaded');

    return () => {
      // Cleanup
      if (document.head.contains(script)) {
        document.head.removeChild(script);
      }
      const analScript = document.getElementById('wf_anal');
      if (analScript && document.head.contains(analScript)) {
        document.head.removeChild(analScript);
      }
    };
  }, []);

  // Initialize intl-tel-input
  useEffect(() => {
    if (phoneInputRef.current && !itiRef.current) {
      console.log('🔧 Initializing intl-tel-input...');
      
      itiRef.current = intlTelInput(phoneInputRef.current, {
        initialCountry: "in",
        separateDialCode: true,
      });
      
      console.log('✅ intl-tel-input initialized');
    }

    return () => {
      if (itiRef.current) {
        itiRef.current.destroy();
        itiRef.current = null;
      }
    };
  }, []);

  return (
    <section 
      id="catalogue-form" 
      className="relative min-h-screen py-16 sm:py-20 md:py-24"
      style={{
        backgroundImage: "url('/leather%20form%20bg.webp')",
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        backgroundAttachment: 'fixed'
      }}
    >
      {/* Overlay for better readability */}
      <div className="absolute inset-0 bg-charcoal/85"></div>

      <div className="container mx-auto px-4 sm:px-6 relative z-10">
        {/* Header Section */}
        <motion.div
          initial={{ opacity: 1, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-8 sm:mb-12"
        >
          <div className="flex justify-center mb-4">
            
          </div>
          <span className="text-saddle-tan font-serif font-medium tracking-widest uppercase text-xs sm:text-sm drop-shadow-lg">
  {t('catalogueForm.badge')}
</span>

<h2 className="text-3xl sm:text-4xl md:text-5xl text-white mt-3 sm:mt-4 mb-4 sm:mb-6 drop-shadow-lg font-serif">
  {t('catalogueForm.title')} 
  <span className="text-saddle-tan"> {t('catalogueForm.titleHighlight')}</span>
</h2>

<p className="text-base sm:text-lg text-white/90 max-w-2xl mx-auto drop-shadow-lg font-serif">
  {t('catalogueForm.description')}
</p>
        </motion.div>

        {/* Two Column Layout */}
        <div className="grid lg:grid-cols-2 gap-8 lg:gap-12 items-center max-w-7xl mx-auto">
          
          {/* Left Side - Glass Style Form Card */}
          <motion.div
            initial={{ opacity: 1, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="w-full lg:max-w-[480px] mx-auto"
          >
            <div className="bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl p-6 sm:p-8 border border-white/20">
            {/* Zoho CRM Web-to-Lead Form */}
            <div id='crmWebToEntityForm' className='zcwf_lblLeft crmWebToEntityForm'>
              <meta name='viewport' content='width=device-width, initial-scale=1.0' />
              <meta httpEquiv='content-type' content='text/html;charset=UTF-8' />
              
              <form 
                id='webform1224645000000593044' 
                action='https://crm.zoho.in/crm/WebToLeadForm' 
                name='WebToLeads1224645000000593044' 
                method='POST'
                acceptCharset='UTF-8'
                onSubmit={(e) => {
                  e.preventDefault();
                  console.log('🔍 Form onSubmit triggered');
                  
                  // Keep a non-empty phone value even if formatter returns blank.
                  if (itiRef.current && phoneInputRef.current) {
                    const rawPhone = phoneInputRef.current.value.trim();
                    let fullNumber = '';

                    try {
                      fullNumber = itiRef.current.getNumber()?.trim() || '';
                    } catch (error) {
                      console.warn('⚠️ Failed to format phone with intl-tel-input:', error);
                    }

                    if (!fullNumber && rawPhone) {
                      const selectedCountry = itiRef.current.getSelectedCountryData?.();
                      const dialCode = selectedCountry?.dialCode ? `+${selectedCountry.dialCode}` : '';
                      const digitsOnlyPhone = rawPhone.replace(/\D/g, '');
                      fullNumber = dialCode && digitsOnlyPhone ? `${dialCode}${digitsOnlyPhone}` : rawPhone;
                    }

                
                    console.log('📱 Original phone:', rawPhone);
                    console.log('📱 E.164 formatted phone:', fullNumber);

                    phoneInputRef.current.value = fullNumber || rawPhone;
                  }
                  
                  // Validate using Zoho's function
                  // @ts-ignore
                  if (typeof window.checkMandatory1224645000000593044 === 'function') {
                    console.log('✅ Validation function found, executing...');
                    // @ts-ignore
                    const isValid = window.checkMandatory1224645000000593044();
                    console.log('📋 Validation result:', isValid);
                    
                    if (isValid) {
                      console.log('✅ Validation passed - submitting to Zoho CRM');
                      console.log('📤 Action URL:', 'https://crm.zoho.in/crm/WebToLeadForm');
                      console.log('📤 Method: POST');
                      console.log('📤 Will redirect to Zoho thank you page after submission');
                      
                      // Allow form to submit naturally
                      const form = e.currentTarget as HTMLFormElement;
                      
                      // Log form data for debugging
                      const formData = new FormData(form);
                      console.log('📋 Form Data:');
                      formData.forEach((value, key) => {
                        if (key !== 'xnQsjsdp' && key !== 'xmIwtLD') {
                          console.log(`  ${key}: ${value}`);
                        }
                      });
                      
                      // Submit the form programmatically to Zoho
                      setTimeout(() => {
                        form.submit();
                      }, 100);
                    } else {
                      console.log('❌ Validation failed');
                    }
                  } else {
                    console.error('❌ Validation function not found');
                  }
                }}
              >
                {/* Hidden authentication fields - DO NOT REMOVE */}
                <input type='text' style={{ display: 'none' }} name='xnQsjsdp' defaultValue='31c59439bbe1e73f41a62f25028eed81fca98f783dc98f827d9458f721431850' />
                <input type='hidden' name='zc_gad' id='zc_gad' defaultValue='' />
                <input type='text' style={{ display: 'none' }} name='xmIwtLD' defaultValue='8cb319131e4ec44184446abd713bc6c4057c1d7d1bffe4b43b8993b74a39b4ea815f907336c8f60200fb908f7086e113' />
                <input type='text' style={{ display: 'none' }} name='actionType' defaultValue='TGVhZHM=' />
                {/* Remove returnURL to use Zoho's thank you page - localhost won't work */}
                <input type='text' style={{ display: 'none' }} name='aG9uZXlwb3Q' defaultValue='' />

                {/* Form Styles */}
                <style dangerouslySetInnerHTML={{ __html: `
                  #crmWebToEntityForm.zcwf_lblLeft {
                    width: 100%;
                    padding: 0;
                    margin: 0 auto;
                    box-sizing: border-box;
                  }
                  #crmWebToEntityForm.zcwf_lblLeft * {
                    box-sizing: border-box;
                  }
                  .zcwf_lblLeft .zcwf_title {
                    word-wrap: break-word;
                    padding: 0 0 20px;
                    font-weight: 600;
                    font-size: 1.5rem;
                    color: #2c1810;
                    font-family: 'Playfair Display', serif;
                    text-align: center;
                  }
                  .zcwf_lblLeft .zcwf_row {
                    margin: 20px 0;
                  }
                  .zcwf_lblLeft .zcwf_col_lab {
                    width: 100%;
                    word-break: break-word;
                    padding: 0 0 8px;
                    margin: 0;
                    font-size: 14px;
                    font-weight: 500;
                    color: #2c1810;
                  }
                  .zcwf_lblLeft .zcwf_col_lab label {
                    display: block;
                  }
                  .zcwf_lblLeft .zcwf_col_fld {
                    width: 100%;
                    padding: 0;
                    position: relative;
                  }
                  .zcwf_lblLeft .zcwf_col_fld input[type=text] {
                    width: 100%;
                    border: 1px solid #d4d4d4;
                    resize: vertical;
                    border-radius: 8px;
                    padding: 12px 16px;
                    font-size: 14px;
                    transition: all 0.2s;
                  }
                  .zcwf_lblLeft .zcwf_col_fld input[type=text]:focus {
                    outline: none;
                    border-color: #b8845b;
                    box-shadow: 0 0 0 3px rgba(184, 132, 91, 0.1);
                  }
                  .zcwf_lblLeft .zcwf_col_fld select,
                  .zcwf_lblLeft .zcwf_col_fld_slt {
                    width: 100%;
                    border: 1px solid #d4d4d4;
                    border-radius: 8px;
                    padding: 12px 16px;
                    font-size: 14px;
                    background: white;
                    transition: all 0.2s;
                    cursor: pointer;
                  }
                  .zcwf_lblLeft .zcwf_col_fld select:focus,
                  .zcwf_lblLeft .zcwf_col_fld_slt:focus {
                    outline: none;
                    border-color: #b8845b;
                    box-shadow: 0 0 0 3px rgba(184, 132, 91, 0.1);
                  }
                  .zcwf_lblLeft .zcwf_col_help {
                    display: none;
                  }
                  .zcwf_lblLeft .zcwf_row:after,
                  .zcwf_lblLeft .zcwf_col_fld:after {
                    content: '';
                    display: table;
                    clear: both;
                  }
                  .zcwf_lblLeft .formsubmit {
                    margin-right: 8px;
                    cursor: pointer;
                    font-size: 14px;
                    padding: 12px 32px;
                    border-radius: 8px;
                    border: none;
                    transition: all 0.2s;
                  }
                  .zcwf_lblLeft .formsubmit.zcwf_button {
                    background: #b8845b;
                    color: white !important;
                    font-weight: 500;
                  }
                  .zcwf_lblLeft .formsubmit.zcwf_button:hover {
                    background: #a16d45;
                    transform: translateY(-1px);
                    box-shadow: 0 4px 12px rgba(184, 132, 91, 0.3);
                  }
                  .zcwf_lblLeft .formsubmit.zcwf_button:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                  }
                  .zcwf_lblLeft .zcwf_button[type=reset] {
                    background: transparent;
                    color: #2c1810;
                    border: 1px solid #d4d4d4;
                    padding: 12px 24px;
                  }
                  .zcwf_lblLeft .zcwf_button[type=reset]:hover {
                    background: #f5f5f5;
                  }
                  @media all and (max-width: 600px) {
                    .zcwf_lblLeft .zcwf_col_lab,
                    .zcwf_lblLeft .zcwf_col_fld {
                      width: 100%;
                      float: none !important;
                    }
                    .zcwf_lblLeft .formsubmit {
                      width: 100%;
                      margin-bottom: 8px;
                    }
                  }
                  
                  /* intl-tel-input custom styles */
                  .iti {
                    width: 100%;
                    display: block;
                  }
                  .iti__tel-input {
                    width: 100% !important;
                    border: 1px solid #d4d4d4 !important;
                    border-radius: 8px !important;
                    padding: 12px 16px 12px 100px !important;
                    font-size: 14px !important;
                    transition: all 0.2s;
                    box-sizing: border-box !important;
                  }
                  .iti__tel-input:focus {
                    outline: none !important;
                    border-color: #b8845b !important;
                    box-shadow: 0 0 0 3px rgba(184, 132, 91, 0.1) !important;
                  }
                  .iti__flag-container {
                    border-right: 1px solid #d4d4d4;
                  }
                  .iti__selected-flag {
                    padding: 0 8px 0 12px;
                  }
                  .iti__selected-dial-code {
                    margin-left: 6px;
                    font-size: 14px;
                    color: #555;
                  }
                  .iti__country-list {
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    max-height: 200px;
                  }
                  .iti__country:hover {
                    background-color: rgba(184, 132, 91, 0.1);
                  }
                  .iti__country.iti__highlight {
                    background-color: rgba(184, 132, 91, 0.2);
                  }
                `}} />

                {/* Form Title */}
                <div className='zcwf_title'>{t('catalogueForm.formTitle')}</div>

                {/* Name Field */}
                <div className='zcwf_row'>
                  <div className='zcwf_col_lab'>
                    <label htmlFor='Last_Name'>
                      {t('catalogueForm.name')} <span style={{ color: 'red' }}>*</span>
                    </label>
                  </div>
                  <div className='zcwf_col_fld'>
                    <input 
                      type='text' 
                      id='Last_Name' 
                      name='Last Name' 
                      maxLength={80}
                      aria-required='true'
                      aria-label='Last Name'
                      style={{ fontFamily: 'Bold, sans-serif' }}
                    />
                  </div>
                </div>

                {/* Phone Field */}
<div className='zcwf_row'>
  <div className='zcwf_col_lab'>
    <label htmlFor='Phone'>
      {t('catalogueForm.phone')} <span style={{ color: 'red' }}>*</span>
    </label>
  </div>
  <div className='zcwf_col_fld'>
    <input 
      ref={phoneInputRef}
      type='text' 
      id='Phone' 
      name='Phone' 
      maxLength={30}
      aria-required='true'
      aria-label='Phone'
      style={{ fontFamily: 'Bold, sans-serif' }}
    />
  </div>
</div>

                {/* Company Field */}
                <div className='zcwf_row'>
                  <div className='zcwf_col_lab'>
                    <label htmlFor='Company'>
                      {t('catalogueForm.company')} <span style={{ color: 'red' }}>*</span>
                    </label>
                  </div>
                  <div className='zcwf_col_fld'>
                    <input 
                      type='text' 
                      id='Company' 
                      name='Company' 
                      maxLength={200}
                      aria-required='true'
                      aria-label='Company'
                      style={{ fontFamily: 'Bold, sans-serif' }}
                    />
                  </div>
                </div>

                {/* Email Field */}
                <div className='zcwf_row'>
                  <div className='zcwf_col_lab'>
                    <label htmlFor='Email'>
                      {t('catalogueForm.email')} <span style={{ color: 'red' }}>*</span>
                    </label>
                  </div>
                  <div className='zcwf_col_fld'>
                    <input 
                      type='text' 
                      id='Email' 
                      name='Email' 
                      maxLength={100}
                      aria-required='true'
                      aria-label='Email'
                      // @ts-ignore
                      ftype='email'
                      autoComplete='false'
                      style={{ fontFamily: 'Bold, sans-serif' }}
                    />
                  </div>
                </div>

                {/* Message Field */}
                <div className='zcwf_row'>
                  <div className='zcwf_col_lab'>
                    <label htmlFor='Fax'>{t('catalogueForm.message')}</label>
                  </div>
                  <div className='zcwf_col_fld'>
                    <input 
                      type='text' 
                      id='Fax' 
                      name='Fax' 
                      maxLength={30}
                      aria-required='false'
                      aria-label='Fax'
                      style={{ fontFamily: 'Bold, sans-serif' }}
                    />
                  </div>
                </div>

                {/* Submit and Reset Buttons */}
                <div className='zcwf_row'>
                  <div className='zcwf_col_lab'></div>
                  <div className='zcwf_col_fld'>
                    <input 
                      type='submit' 
                      id='formsubmit' 
                      className='formsubmit zcwf_button' 
                      defaultValue={t('catalogueForm.submit')} 
                      title='Submit'
                    />
                    <input 
                      type='reset' 
                      className='zcwf_button' 
                      name='reset' 
                      defaultValue={t('catalogueForm.reset')} 
                      title='Reset'
                    />
                  </div>
                </div>
              </form>
            </div>

            {/* Additional Info */}
            <div className="mt-8 text-center border-t pt-6 border-charcoal/10">
              <div className="flex items-center justify-center gap-2 text-sm text-charcoal/60">
                <Download className="w-4 h-4 text-saddle-tan" />
                <p>{t('catalogueForm.afterSubmit')}</p>
              </div>
            </div>
            </div>
          </motion.div>

          {/* Right Side - Animated Catalogue Book Showcase */}
          <motion.div
            initial={{ opacity: 1, x: 30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="hidden lg:flex items-center justify-center"
          >
            <div className="relative w-full max-w-2xl">
              {/* Catalogue Design Showcase Grid */}
              <div className="grid grid-cols-2 gap-6">
                {/* Product 1 - Bag */}
                <motion.div
                  initial={{ opacity: 1, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: 0.5 }}
                  className="relative group"
                >
                  <div className="animate-float-delayed-1 bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20 hover:bg-white/20 transition-all duration-300">
                    <img 
                      src={bagImage1.src}
                      alt="Leather Tote Bag" 
                      className="w-full h-48 object-cover rounded-lg drop-shadow-lg transform group-hover:scale-110 transition-transform duration-500"
                    />
                    <p className="text-white text-sm font-medium text-center mt-3">Structured Tote</p>
                  </div>
                </motion.div>

                {/* Product 2 - Wallet */}
                <motion.div
                  initial={{ opacity: 1, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: 0.6 }}
                  className="relative group"
                >
                  <div className="animate-float-delayed-2 bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20 hover:bg-white/20 transition-all duration-300">
                    <img 
                      src={walletImage1.src}
                      alt="Leather Wallet" 
                      className="w-full h-48 object-cover rounded-lg drop-shadow-lg transform group-hover:scale-110 transition-transform duration-500"
                    />
                    <p className="text-white text-sm font-medium text-center mt-3">Classic Wallet</p>
                  </div>
                </motion.div>

                {/* Product 3 - Belt */}
                <motion.div
                  initial={{ opacity: 1, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: 0.7 }}
                  className="relative group"
                >
                  <div className="animate-float-delayed-3 bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20 hover:bg-white/20 transition-all duration-300">
                    <img 
                      src={beltImage1.src}
                      alt="Leather Belt" 
                      className="w-full h-48 object-cover rounded-lg drop-shadow-lg transform group-hover:scale-110 transition-transform duration-500"
                    />
                    <p className="text-white text-sm font-medium text-center mt-3">Leather Belt</p>
                  </div>
                </motion.div>

                {/* Product 4 - Travel Bag */}
                <motion.div
                  initial={{ opacity: 1, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: 0.8 }}
                  className="relative group"
                >
                  <div className="animate-float-delayed-4 bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20 hover:bg-white/20 transition-all duration-300">
                    <img 
                      src={travelBagImage.src}
                      alt="Leather Travel Duffel" 
                      className="w-full h-48 object-cover rounded-lg drop-shadow-lg transform group-hover:scale-110 transition-transform duration-500"
                    />
                    <p className="text-white text-sm font-medium text-center mt-3">Travel Duffel</p>
                  </div>
                </motion.div>
              </div>

              {/* Decorative glow effect */}
              <div className="absolute -z-10 inset-0 bg-gradient-to-br from-saddle-tan/30 via-transparent to-saddle-tan/20 blur-3xl"></div>
              
              {/* Info badge */}
              <div className="mt-6 text-center">
                <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full border border-white/20">
                  <FileText className="w-4 h-4 text-saddle-tan" />
                  <span className="text-white text-sm font-medium">100+ Designs in Our Catalogue</span>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Mobile Catalogue Image - Shown below form on smaller screens */}
          <motion.div
            initial={{ opacity: 1, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="lg:hidden flex items-center justify-center"
          >
            <div className="relative w-full max-w-md">
              {/* Mobile: 2-column grid with 4 products */}
              <div className="grid grid-cols-2 gap-4">
                {/* Product 1 */}
                <div className="animate-float-delayed-1 bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
                  <img 
                    src={bagImage1.src}
                    alt="Leather Tote Bag" 
                    className="w-full h-32 object-cover rounded-lg drop-shadow-lg"
                  />
                  <p className="text-white text-xs font-medium text-center mt-2">Structured Tote</p>
                </div>

                {/* Product 2 */}
                <div className="animate-float-delayed-2 bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
                  <img 
                    src={walletImage1.src}
                    alt="Leather Wallet" 
                    className="w-full h-32 object-cover rounded-lg drop-shadow-lg"
                  />
                  <p className="text-white text-xs font-medium text-center mt-2">Classic Wallet</p>
                </div>

                {/* Product 3 */}
                <div className="animate-float-delayed-3 bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
                  <img 
                    src={beltImage1.src}
                    alt="Leather Belt" 
                    className="w-full h-32 object-cover rounded-lg drop-shadow-lg"
                  />
                  <p className="text-white text-xs font-medium text-center mt-2">Leather Belt</p>
                </div>

                {/* Product 4 */}
                <div className="animate-float-delayed-4 bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
                  <img 
                    src={travelBagImage.src}
                    alt="Leather Travel Duffel" 
                    className="w-full h-32 object-cover rounded-lg drop-shadow-lg"
                  />
                  <p className="text-white text-xs font-medium text-center mt-2">Travel Duffel</p>
                </div>
              </div>

              {/* Mobile Info badge */}
              <div className="mt-4 text-center">
                <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm px-3 py-1.5 rounded-full border border-white/20">
                  <FileText className="w-3 h-3 text-saddle-tan" />
                  <span className="text-white text-xs font-medium">100+ Designs</span>
                </div>
              </div>
            </div>
          </motion.div>

        </div>
      </div>

      {/* CSS for floating animation */}
      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes float {
          0%, 100% {
            transform: translateY(0px);
          }
          50% {
            transform: translateY(-20px);
          }
        }
        
        .animate-float {
          animation: float 6s ease-in-out infinite;
        }

        .animate-float-delayed-1 {
          animation: float 6s ease-in-out infinite;
          animation-delay: 0s;
        }

        .animate-float-delayed-2 {
          animation: float 6s ease-in-out infinite;
          animation-delay: 0.5s;
        }

        .animate-float-delayed-3 {
          animation: float 6s ease-in-out infinite;
          animation-delay: 1s;
        }

        .animate-float-delayed-4 {
          animation: float 6s ease-in-out infinite;
          animation-delay: 1.5s;
        }
      `}} />
    </section>
  );
};

