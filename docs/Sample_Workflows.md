# Sample Workflows: Chaining Multiple Endpoints for Impactful Insights

Below are some example **workflows** that demonstrate how you might **chain** these various government-data endpoints—across **Congress.gov**, **FEC**, **Regulations.gov**, and the **Senate Lobbying Disclosure (LDA)**—to gather richer, more impactful information. Each workflow taps into multiple APIs, linking bills, dockets, lobbying data, member information, and campaign finances for a comprehensive view.

---

## 1. Follow a Bill from Introduction to Lobbying Activities

### Step 1: Identify a Bill on Congress.gov

1. **List the most recent bills** from Congress.gov using `/bill`.  
   - Retrieve title, sponsor, and the Congress number (e.g., `117` or `119`).  
2. **Fetch details for that bill** using `/bill/{congress}/{billType}/{billNumber}`.  
   - Gather official summary, policy area, and sponsor ID (the member who introduced the bill).

### Step 2: Check for Lobbying Filings on the Same Issue

1. **Look up the policy or issue codes** from the Bill’s subject:  
   - If the Bill is labeled under “Telecommunications,” for instance, map that to the relevant lobbying issue code (like `TEC` or `TEL`) from LDA’s `/constants/filing/lobbyingactivityissues/`.
2. **Search LDA Filings** via `/filings/?filing_specific_lobbying_issues=Telecommunications` (or another relevant text filter).  
   - Use `page_size` plus optional year filters to see if any organizations reported lobbying on that topic.  
3. **Expand** each filing detail with `/filings/{filing_uuid}/` to see which clients or registrants are actively lobbying on the domain of the bill.

### Step 3: Analyze Potential Influence on the Bill

- Cross-reference **lobbying clients** or **registrants** found in Step 2 with any related **FEC** data on committees or contributions (see Workflow #2 below).  
- If the sponsor or co-sponsor of the bill is also receiving political contributions from the identified lobbying entities, that might suggest deeper alignment or influence.

**Impact:** This chain reveals **who is lobbying** on an issue, while you see how that issue is shaping legislation in real time.

---

## 2. Connect FEC Campaign Finance Records with Lobbying Disclosure

### Step 1: Pick a Candidate from FEC

1. **Search for a candidate** using `/candidates` in the FEC API.  
   - For example, retrieve “WALSH, MONTANA” or “SMITH, KENTUCKY.”  
   - Grab the candidate’s committees or relevant cycle-year ID.

### Step 2: Retrieve Contributions and Disbursements

1. **Fetch itemized receipts** with `/getItemizedReceipts` to see who contributed to the candidate’s committee.  
   - Example: You find a corporate PAC donated \$10,000.  
2. **Query itemized disbursements** via `/getItemizedDisbursements` to check how the campaign spent funds.

### Step 3: Match Contributors with Lobbying Filings

1. **Look up** that corporate PAC or entity in the **Senate Lobbying Disclosure** endpoint: 
   - Use `/registrants/` or `/clients/` if the contributor name resembles a lobbying registrant or client.  
   - You might discover the same corporation’s lobbyists filed on an issue that the candidate’s committee championed in legislation.

**Impact:** This chain shows how **campaign contributions** might relate to **lobbying** by the same organizations, giving a fuller picture of influence and alliances.

---

## 3. Combining Committee Reports with Lobbying & Congressional Records

### Step 1: Retrieve Recent Committee Reports from Congress.gov

- Use `/committee-reports` to see if a House or Senate committee has released a report (e.g., H. Rept. 118-817).

### Step 2: Cross-Check Filings from LDA

- If the report is about a certain domain (like “Energy” or “Budget/Appropriations”), check LDA’s `/filings/?filing_specific_lobbying_issues=Energy`.  
- Identify which registrants or clients are lobbying on appropriations or energy issues.

### Step 3: Expand with Congressional Record

- For the same date or legislative day cited in the committee report, retrieve the **Congressional Record** from `/congressionalRecord` to see if relevant debates mention certain lobbyists or points of contention.  
- Potentially see if those same committees had members sponsoring or opposing the measure in question.

**Impact:** This chain clarifies how **committee findings** and **floor debates** might be influenced by or correlated with **lobbying efforts** on the same topics.

---

## 4. Tracking a Proposed Federal Rule, Public Comments, and Lobbying

### Step 1: Identify a Regulatory Docket in Regulations.gov

- Query `/listDockets` for an agency’s new rule or notice (e.g., an FDA docket on “Withdrawal of Compliance Policy Guide”).  
- Gather the docket ID: `FDA-2019-N-4611`, for instance.

### Step 2: See Which Lobbyists Are Engaged

- In the **LDA Filings** endpoint, search for `client_name=FDA` or a specific mention of “compliance policy” in `filing_specific_lobbying_issues`.  
- Alternatively, search the `government_entities` field for “Food and Drug Administration” in `/filings/`.

### Step 3: Review Public Comments on the Same Docket

- Use `/listComments` (Regulations.gov) to see individuals, orgs, or lobbying groups that publicly commented.  
- Possibly align them with LDA **registrant** or **client** data—some orgs might have filed both a lobbying registration and submitted official comments.

**Impact:** This chain clarifies how **rulemaking** and **public commentary** connect to **lobbying** at the agency level, revealing a holistic view of who’s trying to shape regulatory actions.

---

## 5. Member of Congress & Bill Sponsorship vs. Lobbying Clients

### Step 1: Pull Congressional Member Data

- Use Congress.gov `/members` to find a House or Senate member (e.g., “Michael Waltz” in Florida).  
- Grab the `memberID` or external reference ID.

### Step 2: Which Bills Has This Member Sponsored?

- Query `/bill` or `/bill/{congress}/{billType}/{billNumber}` with sponsor or co-sponsor info to see which bills they introduced or supported.

### Step 3: Check LDA for Overlap

- If a Bill deals with, say, “National Security,” see if there are **LD1/LD2** records on “NAT” (Natural Resources) or “DEF” (Defense) issues that might reference Florida-based clients.  
- Potential synergy if the same sponsor is pushing legislation that Florida defense contractors are lobbying on.

**Impact:** This chain helps identify **geographic** or **thematic** alignment between a lawmaker’s activities and the lobbying interests in their district, shining a light on local or industry-specific influences.

---

## 6. Legislative Amendments Tied to FEC Donors and LDA Filings

### Step 1: Check Amendments on a Key Bill

- Use `/bill/{congress}/{billType}/{billNumber}/amendments` from Congress.gov to see all proposed amendments, who introduced them, and any voting records.

### Step 2: Cross-Reference FEC for Those Amendments’ Sponsors

- For each sponsor, retrieve their FEC candidate ID and see if any major donors align with the amendment’s purpose.  
- For instance, a sponsor who proposed a “Healthcare” amendment might receive large contributions from medical associations.

### Step 3: See if the Associations Are Lobbying for This Amendment

- Jump into LDA: `/filings/?client_name=American Medical Association` (for example).  
- If they have recent lobbying activities specifically mentioning the same legislative focus as the proposed amendment, you’ve found a direct link between the contributor and legislative action.

**Impact:** This chain reveals how a single **amendment** can link to outside influences, bridging campaign finance, direct lobbying, and legislative proposals.

---

## Why These Workflows Matter

- **Transparency:** Combining campaign finance (FEC), lobbying (Senate LDA), legislative data (Congress.gov), and regulatory dockets (Regulations.gov) can expose how public policy is shaped across multiple channels.
- **Deep Insights:** Investigative journalists, civic hackers, and policy analysts get a 360° view of how bills and regulations evolve, and who’s fueling that evolution.
- **Policy Efficacy:** By seeing whether certain bills or rules gather broad support vs. special-interest push, you can gauge potential outcomes and impacts.
