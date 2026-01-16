import logging
from typing import Any, Dict, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch

logger = logging.getLogger("ips-generator")


class IPSPDFRenderer:
    """
    Renders FHIR IPS Bundles into human-readable PDF documents.
    """

    def __init__(self) -> None:
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self) -> None:
        self.styles.add(
            ParagraphStyle(
                name="IPSHeader",
                parent=self.styles["Heading1"],
                fontSize=18,
                spaceAfter=12,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Heading2"],
                fontSize=14,
                spaceBefore=12,
                spaceAfter=6,
                textColor=colors.darkblue,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="Label",
                parent=self.styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=10,
            )
        )

    def render_to_file(self, bundle: Dict[str, Any], output_path: str) -> None:
        """
        Generates a PDF file at output_path from the provided bundle.
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        story: List[Any] = []

        # 1. Extract Data
        patient = self._find_resource(bundle, "Patient")
        practitioner = self._find_resource(bundle, "Practitioner")

        # 2. Document Header
        story.append(
            Paragraph("International Patient Summary", self.styles["IPSHeader"])
        )
        story.append(
            Paragraph(
                f"Date: {bundle.get('timestamp', 'Unknown')}", self.styles["Normal"]
            )
        )
        story.append(Spacer(1, 0.2 * inch))

        # 3. Patient Info Section
        if patient:
            self._add_patient_section(story, patient)

        # 4. Author Info
        if practitioner:
            story.append(Spacer(1, 0.1 * inch))
            name = practitioner.get("name", [{}])[0]
            p_name = f"{name.get('given', [''])[0]} {name.get('family', '')}"
            story.append(
                Paragraph(f"<b>Author:</b> Dr. {p_name}", self.styles["Normal"])
            )

        story.append(Spacer(1, 0.3 * inch))

        # 5. Clinical Sections
        self._add_clinical_section(
            story, bundle, "Allergies and Intolerances", "AllergyIntolerance"
        )
        self._add_clinical_section(
            story, bundle, "Medication Summary", "MedicationStatement"
        )
        self._add_clinical_section(story, bundle, "Problem List", "Condition")

        # Build
        try:
            doc.build(story)
            logger.debug(f"PDF generated: {output_path}")
        except Exception as e:
            logger.error(f"Failed to build PDF {output_path}: {e}")
            raise

    def _find_resource(self, bundle: Dict[str, Any], resource_type: str) -> Any:
        for entry in bundle.get("entry", []):
            if entry.get("resource", {}).get("resourceType") == resource_type:
                return entry["resource"]
        return None

    def _find_resources(self, bundle: Dict[str, Any], resource_type: str) -> List[Any]:
        return [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == resource_type
        ]

    def _add_patient_section(self, story: List[Any], patient: Dict[str, Any]) -> None:
        name = patient.get("name", [{}])[0]
        full_name = f"{name.get('family', '')}, {name.get('given', [''])[0]}"

        data = [
            ["Patient Name:", full_name],
            ["Birth Date:", patient.get("birthDate", "Unknown")],
            ["Gender:", patient.get("gender", "Unknown").capitalize()],
            ["ID:", patient.get("id", "Unknown")],
        ]

        table = Table(data, colWidths=[1.5 * inch, 4 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        story.append(Paragraph("Patient Demographics", self.styles["SectionHeader"]))
        story.append(table)

    def _add_clinical_section(
        self, story: List[Any], bundle: Dict[str, Any], title: str, resource_type: str
    ) -> None:
        resources = self._find_resources(bundle, resource_type)
        if not resources:
            return

        story.append(Paragraph(title, self.styles["SectionHeader"]))

        # Table Header
        table_data = [["Code / Description", "Status", "System"]]

        for res in resources:
            coding = self._extract_coding(res)
            status = self._extract_status(res)

            display = coding.get("display", "Unknown Code")
            code = coding.get("code", "")
            system = coding.get("system", "").split("/")[-1]  # Simplify system URL

            row_text = f"{display} ({code})"
            table_data.append([row_text, status, system])

        t = Table(table_data, colWidths=[3.5 * inch, 1 * inch, 1.5 * inch])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )
        story.append(t)
        story.append(Spacer(1, 0.1 * inch))

    def _extract_coding(self, resource: Dict[str, Any]) -> Dict[str, str]:
        # Handle difference between Condition.code and
        # MedicationStatement.medicationCodeableConcept
        if "code" in resource:
            return resource["code"].get("coding", [{}])[0]
        elif "medicationCodeableConcept" in resource:
            return resource["medicationCodeableConcept"].get("coding", [{}])[0]
        return {}

    def _extract_status(self, resource: Dict[str, Any]) -> str:
        # Handle ClinicalStatus object vs string status
        if "clinicalStatus" in resource:
            return (
                resource["clinicalStatus"].get("coding", [{}])[0].get("code", "unknown")
            )
        return resource.get("status", "unknown")
