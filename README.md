# InsightsGPT

### Making Government Data Accessible and Actionable

**InsightsGPT** is an open-source project designed to provide transparent, easy-to-access insights into U.S. legislative, regulatory, and campaign finance activities. By leveraging the power of generative AI, InsightsGPT bridges the gap between complex datasets and the people who need them most. Whether you're a journalist, researcher, activist, or curious citizen, InsightsGPT empowers you to explore government data with ease.

---

## **Key Features**

### **Congress.gov Integration**
- Access detailed legislative information, including:
  - Bills and amendments
  - Legislative actions
  - Committee reports
  - Nominations and treaties
  - Congressional records

### **FEC Integration**
- Explore campaign finance data:
  - Track contributions to candidates and committees.
  - Analyze itemized receipts and disbursements.
  - Review committee activities and expenditures.

### **Regulations.gov Integration**
- Engage with regulatory processes:
  - Search for dockets and associated documents.
  - Access public comments and analyze sentiment.
  - Explore regulatory proposals across federal agencies.

### **AI-Powered Analysis**
- Natural language querying for complex datasets.
- Automated summaries of bills, financial reports, and regulatory actions.
- Customizable visualizations for data insights.

---

## **Getting Started**

### **Prerequisites**
- Python 3.7+
- API keys for:
  - [Congress.gov API](https://api.congress.gov)
  - [OpenFEC API](https://api.open.fec.gov/developers/)
  - [Regulations.gov API](https://open.gsa.gov/api/regulationsgov/)

### **Installation**
1. Clone the repository:
   ```bash
   git clone https://github.com/CongressionalInsights/InsightsGPT.git
   cd InsightsGPT
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your API keys in the `.env` file:
   ```env
   CONGRESS_API_KEY=your_congress_api_key
   FEC_API_KEY=your_fec_api_key
   REGULATIONS_API_KEY=your_regulations_api_key
   ```
4. Run tests to ensure setup is complete:
   ```bash
   pytest
   ```

---

## **How It Works**

InsightsGPT integrates data from three key government sources:

1. **Congress.gov API**
   - Provides legislative data, including bills, amendments, nominations, and committee reports.
   - Example Use Case:
     - *Track amendments to a bill and their outcomes.*

2. **FEC API**
   - Offers detailed campaign finance data, including contributions and expenditures.
   - Example Use Case:
     - *Analyze donations to a candidate by location.*

3. **Regulations.gov API**
   - Gives access to regulatory dockets, public comments, and federal rules.
   - Example Use Case:
     - *Examine public sentiment on proposed regulations for artificial intelligence.*

---

## **Usage Examples**

### Query a Bill’s Details:
```python
from insights_gpt import CongressAPI

congress_api = CongressAPI(api_key="your_congress_api_key")
bill_details = congress_api.get_bill_details(congress=118, bill_type="hr", bill_number=3075)
print(bill_details)
```

### Analyze Campaign Contributions:
```python
from insights_gpt import FECAPI

fec_api = FECAPI(api_key="your_fec_api_key")
receipts = fec_api.get_itemized_receipts(contributor_name="John Doe", cycle=2024)
print(receipts)
```

### Explore Public Comments:
```python
from insights_gpt import RegulationsAPI

regulations_api = RegulationsAPI(api_key="your_regulations_api_key")
comments = regulations_api.list_comments(search_term="Artificial Intelligence", page_size=10)
print(comments)
```

---

## **Contributing**

We welcome contributions from everyone! Please see our [CONTRIBUTING.md](https://github.com/CongressionalInsights/InsightsGPT/blob/main/CONTRIBUTING.md) for guidelines on how to get started.

---

## **Roadmap**

### Planned Features:
- Integration with additional APIs, including GovInfo.gov.
- Advanced visualization tools for campaign finance data.
- Support for natural language queries across all endpoints.
- Enhanced documentation and tutorials.

---

## **License**
This project is licensed under the MIT License. See the [LICENSE](https://github.com/CongressionalInsights/InsightsGPT/blob/main/LICENSE) file for details.

---

## **Acknowledgments**

A special thanks to:
- [Congress.gov](https://www.congress.gov/)
- [OpenFEC](https://www.fec.gov/data/)
- [Regulations.gov](https://www.regulations.gov/)
- The open-source community for making this project possible.
