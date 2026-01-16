import logging
from typing import Any, Dict, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch

logger = logging.getLogger("ips-generator")


class IPSPDFRenderer:
    """
    Renders FHIR IPS Bundles into human-readable PDF documents.
    Supports core and optional sections.
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

    def render_to_file(self, bundle: Dict[str, Any], output_path: str) -> None:
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        story: List[Any] = []

        # 1. Header
        story.append(
            Paragraph("International Patient Summary", self.styles["IPSHeader"])
        )
        story.append(
            Paragraph(
                f"Generated: {bundle.get('timestamp', 'Unknown')}",
                self.styles["Normal"],
            )
        )
        story.append(Spacer(1, 0.2 * inch))

        # 2. Patient
        patient = self._find_resource(bundle, "Patient")
        if patient:
            self._add_patient_section(story, patient)

        story.append(Spacer(1, 0.2 * inch))

        # 3. Clinical Sections
        self._add_generic_section(
            story, bundle, "Allergies and Intolerances", "AllergyIntolerance"
        )
        self._add_generic_section(story, bundle, "Problem List", "Condition")
        self._add_generic_section(
            story, bundle, "Medication Summary", "MedicationStatement"
        )
        self._add_generic_section(story, bundle, "Immunizations", "Immunization")
        self._add_generic_section(story, bundle, "Procedures", "Procedure")
        self._add_generic_section(story, bundle, "Medical Devices", "Device")
        self._add_generic_section(story, bundle, "Diagnostic Results", "Observation")

        # Build
        try:
            doc.build(story)
            logger.debug(f"PDF generated: {output_path}")
        except Exception as e:
            logger.error(f"Failed to build PDF {output_path}: {e}")
            raise

    def _find_resource(
        self, bundle: Dict[str, Any], resource_type: str
    ) -> Optional[Dict[str, Any]]:
        for entry in bundle.get("entry", []):
            if entry.get("resource", {}).get("resourceType") == resource_type:
                return entry["resource"]
        return None

    def _find_resources(
        self, bundle: Dict[str, Any], resource_type: str
    ) -> List[Dict[str, Any]]:
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
            ["Gender:", str(patient.get("gender", "Unknown")).capitalize()],
            ["ID:", patient.get("id", "Unknown")],
        ]

        table = Table(data, colWidths=[1.5 * inch, 4 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        story.append(Paragraph("Patient Demographics", self.styles["SectionHeader"]))
        story.append(table)

    def _add_generic_section(
        self, story: List[Any], bundle: Dict[str, Any], title: str, resource_type: str
    ) -> None:
        """
        Generic renderer for any clinical section.
        Extracts code/display and status/date where available.
        """
        resources = self._find_resources(bundle, resource_type)
        if not resources:
            return

        story.append(Paragraph(title, self.styles["SectionHeader"]))

        # Table Header
        headers = ["Description / Code", "Details", "Date"]
        table_data = [headers]

        for res in resources:
            coding = self._extract_primary_code(res)

            # Column 1: Description
            display = coding.get("display", "Unknown")
            code = coding.get("code", "")
            col1 = f"{display}\n({code})"

            # Column 2: Status or Value
            status = str(res.get("status", ""))
            value = res.get("valueString", "")
            col2 = value if value else status

            # Column 3: Date
            date = self._extract_date(res)

            table_data.append([col1, col2, date])

        t = Table(table_data, colWidths=[3 * inch, 1.5 * inch, 1.5 * inch])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FontSize", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(t)
        story.append(Spacer(1, 0.1 * inch))

    def _extract_primary_code(self, res: Dict[str, Any]) -> Dict[str, str]:
        # Try standard locations for clinical codes
        if "code" in res:
            return res["code"].get("coding", [{}])[0]
        if "vaccineCode" in res:
            return res["vaccineCode"].get("coding", [{}])[0]
        if "medicationCodeableConcept" in res:
            return res["medicationCodeableConcept"].get("coding", [{}])[0]
        if "type" in res:  # For Devices
            return res["type"].get("coding", [{}])[0]
        return {}

    def _extract_date(self, res: Dict[str, Any]) -> str:
        # Try standard locations for dates
        return (
            res.get("onsetDateTime")
            or res.get("effectiveDateTime")
            or res.get("occurrenceDateTime")
            or res.get("performedDateTime")
            or res.get("recordedDate")
            or ""
        )
