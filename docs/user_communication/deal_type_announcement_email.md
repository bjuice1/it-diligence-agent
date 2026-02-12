# Deal Type Awareness - User Announcement Email

**Template Version**: 1.0
**Send Date**: [Immediately after Phase 3 production deployment]
**Audience**: All active users
**Delivery Method**: Email + In-app notification

---

## Email Template (HTML)

**Subject**: New Feature: Deal Type Selection for Accurate Recommendations

```html
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .header { background-color: #0066cc; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; max-width: 600px; margin: 0 auto; }
        .feature-box { background-color: #f0f8ff; border-left: 4px solid #0066cc; padding: 15px; margin: 20px 0; }
        .action-box { background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin: 20px 0; }
        .deal-type { font-weight: bold; color: #0066cc; }
        .footer { background-color: #f5f5f5; padding: 20px; text-align: center; font-size: 12px; color: #666; }
        ul { margin: 10px 0; padding-left: 20px; }
        .cta-button { background-color: #0066cc; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 New Feature: Deal Type Selection</h1>
    </div>

    <div class="content">
        <p>Hi [User Name],</p>

        <p>We're excited to announce a major enhancement to the IT Due Diligence Agent that will provide more accurate and relevant recommendations for your M&A transactions!</p>

        <div class="feature-box">
            <h2>What's New?</h2>
            <p>When creating a deal, you now <strong>select the deal type</strong>:</p>
            <ul>
                <li><span class="deal-type">Acquisition (Integration)</span> - Buyer acquires target company</li>
                <li><span class="deal-type">Carve-Out</span> - Separating business unit from parent company</li>
                <li><span class="deal-type">Divestiture</span> - Clean separation and sale of business unit</li>
            </ul>
        </div>

        <h2>Why This Matters</h2>
        <p>The system now provides <strong>recommendations tailored to your specific deal structure</strong>:</p>

        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <tr style="background-color: #f5f5f5;">
                <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Deal Type</th>
                <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Focus</th>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Acquisitions</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">Consolidation synergies, system integration, cost savings</td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Carve-Outs</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">Separation costs, TSA exposure, standalone capability build-out</td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Divestitures</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">Extraction costs, untangling from parent systems</td>
            </tr>
        </table>

        <h2>Examples of Deal-Specific Recommendations</h2>

        <p><strong>Acquisition (Integration):</strong></p>
        <ul>
            <li>"Consolidate target's AWS environment into buyer's existing cloud platform"</li>
            <li>"Migrate target's 45 applications to buyer's standardized tech stack"</li>
            <li>"Decommission redundant target systems post-integration"</li>
        </ul>

        <p><strong>Carve-Out (Separation):</strong></p>
        <ul>
            <li>"Build standalone AWS environment for target (no consolidation possible)"</li>
            <li>"Establish separate identity management system (cannot rely on parent)"</li>
            <li>"Negotiate TSA for shared services during transition (18-24 months)"</li>
        </ul>

        <div class="action-box">
            <h2>✅ Action Required</h2>
            <p><strong>Please review your existing deals and update deal types if needed:</strong></p>
            <ol>
                <li>Go to the <strong>Deals</strong> page</li>
                <li>Click <strong>Edit</strong> on each deal</li>
                <li>Select the correct <strong>Deal Type</strong> from the dropdown</li>
                <li>Click <strong>Save</strong></li>
                <li><strong>Re-run analysis</strong> to get updated recommendations</li>
            </ol>
            <p style="margin-top: 15px;">
                <a href="[APP_URL]/deals" class="cta-button">Review My Deals</a>
            </p>
        </div>

        <h2>Backward Compatibility</h2>
        <p>All existing deals have been automatically classified as <strong>"Acquisition"</strong> since the system previously assumed integration scenarios. If any of your deals are actually carve-outs or divestitures, please update them to get accurate recommendations.</p>

        <h2>Need Help?</h2>
        <ul>
            <li>📖 <a href="[APP_URL]/docs/user_guide/creating_deals">Updated User Guide</a></li>
            <li>❓ <a href="[APP_URL]/docs/faq">Frequently Asked Questions</a></li>
            <li>💬 <a href="mailto:support@example.com">Contact Support</a></li>
        </ul>

        <p style="margin-top: 30px;">We're confident this enhancement will provide more accurate cost estimates and actionable recommendations for your M&A transactions.</p>

        <p>Thank you,<br>
        <strong>IT DD Team</strong></p>
    </div>

    <div class="footer">
        <p>IT Due Diligence Agent | [Company Name]</p>
        <p>Questions? Reply to this email or contact <a href="mailto:support@example.com">support@example.com</a></p>
    </div>
</body>
</html>
```

---

## Email Template (Plain Text)

**For email clients that don't support HTML:**

```
Subject: New Feature: Deal Type Selection for Accurate Recommendations

Hi [User Name],

We're excited to announce a major enhancement to the IT Due Diligence Agent!

=== WHAT'S NEW? ===

When creating a deal, you now SELECT THE DEAL TYPE:

• Acquisition (Integration) - Buyer acquires target company
• Carve-Out - Separating business unit from parent company
• Divestiture - Clean separation and sale of business unit

=== WHY THIS MATTERS ===

The system now provides recommendations tailored to your specific deal structure:

ACQUISITIONS → Consolidation synergies, system integration, cost savings
CARVE-OUTS → Separation costs, TSA exposure, standalone capability build-out
DIVESTITURES → Extraction costs, untangling from parent systems

=== EXAMPLES ===

Acquisition (Integration):
• "Consolidate target's AWS environment into buyer's existing cloud platform"
• "Migrate target's 45 applications to buyer's standardized tech stack"

Carve-Out (Separation):
• "Build standalone AWS environment for target (no consolidation possible)"
• "Establish separate identity management system (cannot rely on parent)"
• "Negotiate TSA for shared services during transition (18-24 months)"

=== ACTION REQUIRED ===

Please review your existing deals and update deal types if needed:

1. Go to the Deals page
2. Click Edit on each deal
3. Select the correct Deal Type from the dropdown
4. Click Save
5. Re-run analysis to get updated recommendations

All existing deals have been automatically classified as "Acquisition" since the
system previously assumed integration scenarios. If any of your deals are actually
carve-outs or divestitures, please update them to get accurate recommendations.

=== NEED HELP? ===

• Updated User Guide: [APP_URL]/docs/user_guide/creating_deals
• FAQ: [APP_URL]/docs/faq
• Contact Support: support@example.com

Thank you,
IT DD Team

---
IT Due Diligence Agent | [Company Name]
Questions? Reply to this email or contact support@example.com
```

---

## In-App Notification

**Display on next login for all users:**

```
🚀 NEW FEATURE: Deal Type Selection

The IT DD Agent now supports deal-specific recommendations!

Select your deal type (Acquisition, Carve-Out, or Divestiture) to receive
tailored recommendations:
• Acquisitions → Consolidation synergies
• Carve-Outs → Separation costs & TSA planning
• Divestitures → Extraction strategies

ACTION REQUIRED: Review your existing deals and update deal types for
accurate recommendations.

[Learn More] [Review My Deals] [Dismiss]
```

---

## FAQ Addition

**Add to `docs/FAQ.md`:**

### Deal Type Selection

**Q: What's the difference between Acquisition, Carve-Out, and Divestiture?**

A:
- **Acquisition (Integration)**: Buyer acquires the target company and plans to integrate systems. Focus on consolidation synergies and cost savings.
- **Carve-Out**: Separating a business unit from a parent company. The target needs to build standalone capabilities. Focus on separation costs and TSA planning.
- **Divestiture**: Clean separation where a business unit is being sold. Focus on extraction costs and untangling from parent systems.

**Q: What happened to my existing deals?**

A: All existing deals were automatically classified as "Acquisition" since the system previously assumed integration scenarios. If any of your deals are carve-outs or divestitures, please edit them to update the deal type.

**Q: Can I change the deal type after creating a deal?**

A: Yes! Click "Edit" on any deal and select a new deal type from the dropdown. After saving, re-run the analysis to get updated recommendations.

**Q: How does deal type affect the recommendations?**

A:
- **Acquisitions** receive consolidation synergies like "Migrate target systems to buyer platform"
- **Carve-Outs** receive separation guidance like "Build standalone systems" and TSA cost estimates
- **Divestitures** receive extraction guidance like "Untangle from parent infrastructure"

**Q: What if I'm not sure which deal type to select?**

A: Use this decision tree:
- Is the buyer integrating the target into existing operations? → **Acquisition**
- Is a business unit being separated from a parent to operate independently? → **Carve-Out**
- Is a business unit being cleanly separated and sold? → **Divestiture**

Contact support if you need help classifying your deal.

**Q: Will changing the deal type affect my existing analysis results?**

A: Yes. After changing the deal type, you should re-run the analysis to get updated recommendations tailored to the new deal structure. Previous analysis results will remain in history.

---

## Support Ticket Template

**For support team to use when answering deal type questions:**

```
Subject: Deal Type Selection - [User's Question]

Hi [User Name],

Thank you for your question about deal type selection!

[Answer specific question here]

Quick Reference:

ACQUISITION (Integration)
• Use when: Buyer is integrating target into existing operations
• Recommendations: Consolidation synergies, cost savings, system migration
• Example: "Private equity firm acquires SaaS company to integrate into portfolio"

CARVE-OUT (Separation from Parent)
• Use when: Business unit being separated to operate standalone
• Recommendations: Separation costs, TSA planning, standalone build-out
• Example: "Conglomerate selling division to private equity (division relies on parent IT)"

DIVESTITURE (Clean Separation)
• Use when: Business unit being cleanly separated and sold
• Recommendations: Extraction costs, untangling from parent
• Example: "Corporation divesting non-core business unit"

Need more help? Feel free to reply or schedule a call: [CALENDAR_LINK]

Best regards,
IT DD Support Team
```

---

## Rollout Communication Timeline

| Day | Action | Audience |
|-----|--------|----------|
| D-7 | Send heads-up email to power users | Beta testers, admin users |
| D-3 | Send preview email to all users | All users |
| D-0 | Deploy feature to production | - |
| D-0 | Send announcement email | All users |
| D-0 | Show in-app notification | All users on next login |
| D+1 | Monitor support tickets | Support team |
| D+7 | Send reminder email to inactive users | Users who haven't updated deals |
| D+30 | Send success metrics email | All users |

---

## Success Metrics Email (D+30)

**Subject**: Deal Type Feature - 30 Day Success Report

```
Hi [User Name],

It's been 30 days since we launched the Deal Type Selection feature, and we wanted to share
some exciting results:

📊 ADOPTION METRICS
• [X]% of deals now have explicit deal type classification
• [X] carve-out deals identified (previously classified as acquisitions)
• [X] divestiture deals identified

💡 ACCURACY IMPROVEMENTS
• Cost estimates for carve-outs are now 2.5x higher (reflecting real separation costs)
• TSA recommendations automatically included for carve-outs
• [X] users reported more accurate recommendations

Thank you for helping us improve the IT DD Agent!

Questions or feedback? We'd love to hear from you: feedback@example.com

Best regards,
IT DD Team
```

---

**End of User Communication Template**
