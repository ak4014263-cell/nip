# Screenshot Debug Guide

## Overview
The Firefox automation now captures **screenshots at every critical step** during job application to help you understand exactly what's happening and debug any issues.

## Screenshot Location
All screenshots are saved in: `screenshots/apply_debug/`

## Screenshot Naming Convention
Screenshots are named sequentially with descriptive labels:
- Format: `step_{number}_{description}.png`
- Example: `step_01_browser_launched.png`, `step_12_after_login.png`

## Complete Screenshot Flow

### 1. **Browser Initialization**
- `step_01_browser_launched.png` - Initial browser state

### 2. **Login Process**
- `step_02_login_cookies_loaded.png` - If cached cookies exist
- `step_03_login_session_check.png` - Checking if session is still valid
- `step_04_login_session_restored.png` - If session restored successfully (OR)
- `step_04_login_session_expired.png` - If session expired
- `step_05_login_page_loaded.png` - Login page first load
- `step_06_login_page_dom_ready.png` - After DOM is ready
- `step_07_login_cookies_dismissed.png` - After dismissing cookie banners
- `step_08_login_email_field_found.png` - Email field located
- `step_09_login_email_filled.png` - Email entered
- `step_10_login_password_filled.png` - Password entered
- `step_11_login_before_submit_click.png` - Just before clicking submit
- `step_12_login_submit_clicked.png` - Right after clicking submit
- `step_13_login_redirect_complete.png` - After successful login redirect
- `step_14_login_final_page.png` - Final logged-in state
- `step_XX_after_login.png` - Back in main flow

### 3. **Job Page Navigation**
- `step_XX_job_page_initial_load.png` - Job page first loaded
- `step_XX_job_page_after_network_idle.png` - After network requests complete
- `step_XX_after_dismiss_cookies.png` - After dismissing cookies on job page

### 4. **Apply Button Click**
- `step_XX_before_click_apply.png` - Before clicking Apply button
- `step_XX_after_click_apply.png` - Right after clicking Apply button
- `step_XX_modal_opening_2sec.png` - Modal opening (2 seconds wait)
- `step_XX_modal_fully_opened.png` - Modal fully opened (5 seconds total)

### 5. **Form Filling Process**
- `step_XX_before_filling_form.png` - Before starting to fill
- `step_XX_fill_modal_start.png` - Form filling begins
- `step_XX_fill_resume_uploaded.png` - After resume upload (if applicable)
- `step_XX_fill_extracted_N_fields.png` - After extracting N form fields
- `step_XX_fill_ai_success_N_mappings.png` - AI service returned N mappings
- `step_XX_fill_ai_progress_N_fields.png` - Progress screenshots (every 5 fields)
- `step_XX_fill_ai_complete_N_total.png` - All AI fields filled
- `step_XX_fill_using_fallback_mode.png` - If using fallback logic instead of AI
- `step_XX_fill_fallback_textarea_N.png` - Each textarea filled in fallback mode
- `step_XX_fill_fallback_complete_N_total.png` - Fallback filling complete
- `step_XX_after_filling_form.png` - All fields filled

### 6. **Terms Acceptance**
- `step_XX_before_accept_terms.png` - Before accepting terms
- `step_XX_fill_before_accept_terms.png` - Inside fill function, before terms
- `step_XX_fill_after_accept_terms.png` - Inside fill function, after terms
- `step_XX_fill_all_complete_final.png` - Form completely ready
- `step_XX_after_accept_terms.png` - Back in main flow

### 7. **Submission**
- `step_XX_before_submit.png` - Before clicking submit button
- `step_XX_immediately_after_submit_click.png` - Right after submit click
- `step_XX_3sec_after_submit.png` - 3 seconds after submit
- `step_XX_SUCCESS_final_page.png` - Success confirmation page

### 8. **Error Cases**
- `step_XX_ERROR_no_apply_button.png` - Apply button not found
- `step_XX_ERROR_no_submit_button.png` - Submit button not found
- `step_XX_ERROR_no_fields_extracted.png` - No form fields detected
- `step_XX_fill_ai_ERROR_status_XXX.png` - AI service error
- `step_XX_fill_ai_ERROR_unreachable.png` - AI service unreachable
- `step_XX_login_ERROR_email_field_not_found.png` - Login email field missing
- `step_XX_login_ERROR_password_field_not_found.png` - Login password field missing
- `step_XX_login_ERROR_redirect_timeout.png` - Login redirect failed
- `step_XX_EXCEPTION_XXX.png` - Unexpected exception occurred

## Debugging Tips

### 1. **No Apply Button Found**
Look at: `step_XX_before_click_apply.png`
- Check if the job page loaded correctly
- Verify the Apply button is visible on the page
- Check if a different selector is needed

### 2. **Form Not Filling Correctly**
Look at sequence:
- `step_XX_fill_extracted_N_fields.png` - How many fields were detected?
- `step_XX_fill_ai_success_N_mappings.png` - How many AI mappings returned?
- `step_XX_fill_ai_progress_X_fields.png` - Which fields were actually filled?

### 3. **Submit Button Not Working**
Look at:
- `step_XX_before_submit.png` - Is submit button visible and enabled?
- `step_XX_immediately_after_submit_click.png` - Did page change after click?
- `step_XX_3sec_after_submit.png` - What's the final state?

### 4. **Login Issues**
Look at login sequence:
- Check if email/password fields were found
- Verify credentials were entered correctly
- Check if redirect happened after login

### 5. **AI Service Issues**
Look for:
- `fill_ai_ERROR_unreachable` - AI service not running on port 8010
- `fill_ai_ERROR_status_XXX` - AI service returned error
- `fill_using_fallback_mode` - System fell back to hardcoded logic

## Full-Page Screenshots
All screenshots are taken with `full_page=True`, meaning they capture the entire scrollable page, not just the visible viewport. This helps see modals, overlays, and content that might be below the fold.

## Timestamp Information
Each screenshot is numbered sequentially, so you can see the exact order of operations. The counter resets for each new application.

## What to Share When Reporting Issues
When reporting a problem, share:
1. The complete `screenshots/apply_debug/` folder
2. The log output from the console
3. The specific step number where it failed
4. The job URL you were trying to apply to

## Performance Note
Taking screenshots adds ~100-200ms per screenshot. With ~30-40 screenshots per application, expect an additional 3-6 seconds total execution time. This is acceptable for debugging and can be disabled in production if needed.

## Disabling Screenshots (Future)
To disable screenshots in production:
1. Add a parameter `take_screenshots: bool = True` to `apply_to_job()`
2. Wrap all `await take_screenshot()` calls in `if take_screenshots:` checks
3. Pass `take_screenshots=False` when calling the function

## Common Screenshot Patterns

### Successful Application Flow
```
01_browser_launched
02-14_login_sequence
15_job_page_initial_load
...
XX_before_filling_form
XX_fill_modal_start
XX_fill_extracted_8_fields
XX_fill_ai_success_8_mappings
XX_fill_ai_progress_5_fields
XX_fill_ai_complete_8_total
XX_after_filling_form
XX_before_submit
XX_immediately_after_submit_click
XX_3sec_after_submit
XX_SUCCESS_final_page
```

### Failed Application - No Apply Button
```
01_browser_launched
...
XX_before_click_apply  <-- Look here!
XX_ERROR_no_apply_button  <-- Job page doesn't have expected button
```

### Failed Application - AI Service Down
```
...
XX_fill_extracted_8_fields  <-- Fields were found
XX_fill_ai_ERROR_unreachable  <-- AI service not responding
XX_fill_using_fallback_mode  <-- Switched to fallback
XX_fill_fallback_complete_X_total
...
```

## Screenshot Analysis Workflow
1. **Start from the error** - Find the ERROR or EXCEPTION screenshot
2. **Work backwards** - Look at 2-3 screenshots before the error
3. **Check state** - Verify page loaded correctly, elements visible
4. **Compare with success** - Compare to a successful run's screenshots
5. **Identify root cause** - Determine if it's selector, timing, or logic issue

---

**Happy Debugging!** 🐛📸
