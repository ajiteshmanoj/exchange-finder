/**
 * PDF Generator for Exchange Finder Search Results
 * Generates comprehensive multi-page PDF reports
 */

import jsPDF from 'jspdf';
import 'jspdf-autotable';

/**
 * Generate PDF from search results
 * @param {Array} results - Array of UniversityResult objects
 * @param {Array} selectedModules - Selected NTU modules for the search
 * @param {Object} options - Optional configuration
 * @returns {void} - Triggers download
 */
export const generateSearchResultsPDF = (results, selectedModules, options = {}) => {
  const {
    selectedCountries = [],
    selectedSemester = null,
    executionTime = null,
  } = options;

  // Create new PDF document (A4 size)
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 15;
  let yPosition = margin;

  // Colors (NTU brand)
  const ntuBlue = [0, 61, 124]; // #003D7C
  const greenSuccess = [22, 163, 74]; // Tailwind green-600
  const redDanger = [220, 38, 38]; // Tailwind red-600

  // Helper: Add new page if needed
  const checkNewPage = (requiredSpace = 30) => {
    if (yPosition + requiredSpace > pageHeight - margin) {
      doc.addPage();
      yPosition = margin;
      return true;
    }
    return false;
  };

  // Helper: Add page footer
  const addFooter = () => {
    const pageCount = doc.internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.setTextColor(128);
      doc.text(
        `Page ${i} of ${pageCount}`,
        pageWidth / 2,
        pageHeight - 8,
        { align: 'center' }
      );
      doc.text(
        `Generated: ${new Date().toLocaleString()}`,
        margin,
        pageHeight - 8
      );
    }
  };

  // ============= TITLE PAGE =============

  // Header background
  doc.setFillColor(...ntuBlue);
  doc.rect(0, 0, pageWidth, 45, 'F');

  // Title
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(24);
  doc.setFont('helvetica', 'bold');
  doc.text('Exchange University Report', pageWidth / 2, 22, { align: 'center' });

  doc.setFontSize(12);
  doc.setFont('helvetica', 'normal');
  doc.text('NTU Exchange Finder - Module Mapping Results', pageWidth / 2, 32, { align: 'center' });

  yPosition = 55;

  // Search Summary Box
  doc.setFillColor(245, 247, 250);
  doc.roundedRect(margin, yPosition, pageWidth - 2 * margin, 55, 3, 3, 'F');

  doc.setTextColor(0);
  doc.setFontSize(12);
  doc.setFont('helvetica', 'bold');
  doc.text('Search Parameters', margin + 5, yPosition + 8);

  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');

  const moduleList = selectedModules.map(m => m.code || m).join(', ');
  doc.text(`Modules: ${moduleList || 'None selected'}`, margin + 5, yPosition + 18);

  const countryText = selectedCountries.length > 0
    ? selectedCountries.join(', ')
    : 'All Countries';
  doc.text(`Countries: ${countryText}`, margin + 5, yPosition + 28);

  const semesterText = selectedSemester === 1 ? 'Semester 1'
    : selectedSemester === 2 ? 'Semester 2'
    : 'Both Semesters';
  doc.text(`Target Semester: ${semesterText}`, margin + 5, yPosition + 38);

  doc.text(`Universities Found: ${results.length}`, margin + 5, yPosition + 48);

  yPosition += 65;

  // Results Summary
  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...ntuBlue);
  doc.text('Results Summary', margin, yPosition);
  yPosition += 8;

  // Summary table (top 10)
  const summaryData = results.slice(0, 10).map((uni) => [
    `#${uni.rank}`,
    uni.name.length > 35 ? uni.name.substring(0, 35) + '...' : uni.name,
    uni.country,
    `${uni.mappable_count}/${selectedModules.length}`,
    `${uni.coverage_score.toFixed(0)}%`,
  ]);

  doc.autoTable({
    startY: yPosition,
    head: [['Rank', 'University', 'Country', 'Mapped', 'Coverage']],
    body: summaryData,
    theme: 'striped',
    headStyles: {
      fillColor: ntuBlue,
      fontSize: 9,
      fontStyle: 'bold'
    },
    bodyStyles: { fontSize: 8 },
    columnStyles: {
      0: { cellWidth: 15 },
      1: { cellWidth: 70 },
      2: { cellWidth: 35 },
      3: { cellWidth: 20 },
      4: { cellWidth: 22 },
    },
    margin: { left: margin, right: margin },
  });

  yPosition = doc.lastAutoTable.finalY + 10;

  if (results.length > 10) {
    doc.setFontSize(9);
    doc.setTextColor(100);
    doc.text(`... and ${results.length - 10} more universities (see detailed sections below)`, margin, yPosition);
  }

  // ============= DETAILED UNIVERSITY SECTIONS =============

  doc.addPage();
  yPosition = margin;

  // Section Header
  doc.setFillColor(...ntuBlue);
  doc.rect(0, 0, pageWidth, 20, 'F');
  doc.setTextColor(255);
  doc.setFontSize(16);
  doc.setFont('helvetica', 'bold');
  doc.text('Detailed University Results', pageWidth / 2, 13, { align: 'center' });

  yPosition = 30;

  // Iterate through each university
  results.forEach((university) => {
    // Check if we need a new page (estimate space needed)
    const mappableModulesCount = Object.keys(university.mappable_modules || {}).length;
    const estimatedHeight = 50 + (mappableModulesCount * 25);
    checkNewPage(Math.min(estimatedHeight, 100));

    // University Header
    doc.setFillColor(240, 245, 255);
    doc.roundedRect(margin, yPosition, pageWidth - 2 * margin, 20, 2, 2, 'F');

    doc.setTextColor(...ntuBlue);
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    const uniName = university.name.length > 50 ? university.name.substring(0, 50) + '...' : university.name;
    doc.text(`#${university.rank} ${uniName}`, margin + 5, yPosition + 8);

    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(80);
    const cgpaText = university.min_cgpa > 0 ? university.min_cgpa.toFixed(2) : 'N/A';
    doc.text(`${university.country} | CGPA: ${cgpaText} | Sem1: ${university.sem1_spots} spots | Sem2: ${university.sem2_spots} spots`,
      margin + 5, yPosition + 15);

    yPosition += 25;

    // Mappable Modules
    if (university.mappable_modules && Object.keys(university.mappable_modules).length > 0) {
      doc.setFontSize(10);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(...greenSuccess);
      doc.text('Mappable Modules', margin + 5, yPosition);
      yPosition += 5;

      // Create table data for mappable modules
      const mappingTableData = [];
      Object.entries(university.mappable_modules).forEach(([ntuCode, mappings]) => {
        mappings.forEach((mapping, idx) => {
          mappingTableData.push([
            idx === 0 ? ntuCode : '',
            mapping.partner_module_code || '',
            mapping.partner_module_name
              ? (mapping.partner_module_name.length > 40
                ? mapping.partner_module_name.substring(0, 40) + '...'
                : mapping.partner_module_name)
              : '',
            mapping.academic_units || '',
            `S${mapping.semester || '?'}`,
            mapping.status || '',
          ]);
        });
      });

      doc.autoTable({
        startY: yPosition,
        head: [['NTU Module', 'Partner Code', 'Partner Module Name', 'AU', 'Sem', 'Status']],
        body: mappingTableData,
        theme: 'grid',
        headStyles: {
          fillColor: [34, 197, 94], // Green-500
          fontSize: 8,
          fontStyle: 'bold'
        },
        bodyStyles: { fontSize: 7 },
        columnStyles: {
          0: { cellWidth: 22 },
          1: { cellWidth: 25 },
          2: { cellWidth: 68 },
          3: { cellWidth: 12 },
          4: { cellWidth: 12 },
          5: { cellWidth: 20 },
        },
        margin: { left: margin, right: margin },
      });

      yPosition = doc.lastAutoTable.finalY + 5;
    }

    // Unmappable Modules
    if (university.unmappable_modules && university.unmappable_modules.length > 0) {
      checkNewPage(15);

      doc.setFontSize(10);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(...redDanger);
      doc.text('Unmappable Modules: ', margin + 5, yPosition);

      doc.setFont('helvetica', 'normal');
      doc.setTextColor(80);
      const unmappableText = university.unmappable_modules.join(', ');
      doc.text(unmappableText, margin + 45, yPosition);

      yPosition += 8;
    }

    // Remarks
    if (university.remarks) {
      checkNewPage(15);
      doc.setFontSize(8);
      doc.setTextColor(100);
      doc.setFont('helvetica', 'italic');
      const remarksText = university.remarks.length > 100
        ? university.remarks.substring(0, 100) + '...'
        : university.remarks;
      doc.text(`Remarks: ${remarksText}`, margin + 5, yPosition);
      yPosition += 6;
    }

    // Spacing between universities
    yPosition += 10;
  });

  // Add footers to all pages
  addFooter();

  // Generate filename
  const timestamp = new Date().toISOString().slice(0, 10);
  const filename = `Exchange_Report_${timestamp}.pdf`;

  // Download
  doc.save(filename);
};

export default generateSearchResultsPDF;
