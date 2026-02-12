"""Generate a sample physics PDF for testing the Granite pipeline."""

from fpdf import FPDF

pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)

# ── Page 1: Title + Newton's Laws ────────────────────────────────
pdf.add_page()
pdf.set_font("Helvetica", "B", 24)
pdf.cell(0, 15, "Introduction to Classical Mechanics", ln=True, align="C")
pdf.ln(5)
pdf.set_font("Helvetica", "", 12)
pdf.multi_cell(0, 7, (
    "Classical mechanics is the branch of physics that deals with the motion "
    "of macroscopic objects under the influence of forces. It was developed "
    "primarily by Isaac Newton in the 17th century and remains the foundation "
    "for understanding everyday physical phenomena."
))

pdf.ln(8)
pdf.set_font("Helvetica", "B", 18)
pdf.cell(0, 12, "Newton's Three Laws of Motion", ln=True)
pdf.ln(4)

# Law 1
pdf.set_font("Helvetica", "B", 14)
pdf.cell(0, 10, "First Law  -  Law of Inertia", ln=True)
pdf.set_font("Helvetica", "", 12)
pdf.multi_cell(0, 7, (
    "An object at rest stays at rest, and an object in motion stays in motion "
    "at constant velocity, unless acted upon by a net external force.\n\n"
    "Example: A hockey puck sliding on frictionless ice will continue moving "
    "in a straight line at the same speed indefinitely."
))

pdf.ln(4)

# Law 2
pdf.set_font("Helvetica", "B", 14)
pdf.cell(0, 10, "Second Law  -  F = ma", ln=True)
pdf.set_font("Helvetica", "", 12)
pdf.multi_cell(0, 7, (
    "The acceleration of an object is directly proportional to the net force "
    "acting on it and inversely proportional to its mass.\n\n"
    "    F = m * a\n\n"
    "Where:\n"
    "  F = net force (Newtons)\n"
    "  m = mass (kilograms)\n"
    "  a = acceleration (m/s^2)\n\n"
    "Example: Pushing a 10 kg box with a force of 50 N produces an "
    "acceleration of 5 m/s^2."
))

pdf.ln(4)

# Law 3
pdf.set_font("Helvetica", "B", 14)
pdf.cell(0, 10, "Third Law  -  Action and Reaction", ln=True)
pdf.set_font("Helvetica", "", 12)
pdf.multi_cell(0, 7, (
    "For every action, there is an equal and opposite reaction. When object A "
    "exerts a force on object B, object B simultaneously exerts a force equal "
    "in magnitude but opposite in direction on object A.\n\n"
    "Example: A rocket expels gas downward (action), and the gas pushes the "
    "rocket upward (reaction)."
))

# ── Page 2: Energy & Momentum ────────────────────────────────────
pdf.add_page()
pdf.set_font("Helvetica", "B", 18)
pdf.cell(0, 12, "Energy and Work", ln=True)
pdf.ln(4)
pdf.set_font("Helvetica", "", 12)
pdf.multi_cell(0, 7, (
    "Work is done when a force moves an object through a distance:\n\n"
    "    W = F * d * cos(theta)\n\n"
    "Kinetic Energy is the energy of motion:\n\n"
    "    KE = (1/2) * m * v^2\n\n"
    "Potential Energy (gravitational) is stored energy due to height:\n\n"
    "    PE = m * g * h\n\n"
    "The Work-Energy Theorem states that the net work done on an object "
    "equals its change in kinetic energy:\n\n"
    "    W_net = delta KE = KE_final - KE_initial"
))

pdf.ln(8)
pdf.set_font("Helvetica", "B", 18)
pdf.cell(0, 12, "Conservation of Momentum", ln=True)
pdf.ln(4)
pdf.set_font("Helvetica", "", 12)
pdf.multi_cell(0, 7, (
    "Momentum (p) is defined as the product of mass and velocity:\n\n"
    "    p = m * v\n\n"
    "In an isolated system (no external forces), the total momentum "
    "before a collision equals the total momentum after:\n\n"
    "    m1*v1_i + m2*v2_i  =  m1*v1_f + m2*v2_f\n\n"
    "This principle is used to analyse collisions, explosions, and "
    "rocket propulsion."
))

pdf.ln(8)
pdf.set_font("Helvetica", "B", 18)
pdf.cell(0, 12, "Key Formulas Summary", ln=True)
pdf.ln(4)
pdf.set_font("Courier", "", 11)
formulas = [
    "v = u + a*t",
    "s = u*t + (1/2)*a*t^2",
    "v^2 = u^2 + 2*a*s",
    "F = m * a",
    "W = F * d * cos(theta)",
    "KE = (1/2) * m * v^2",
    "PE = m * g * h",
    "p = m * v",
    "Impulse J = F * delta_t = delta_p",
]
for f in formulas:
    pdf.cell(0, 8, f"   {f}", ln=True)

output_path = "sample_physics.pdf"
pdf.output(output_path)
print(f"Created {output_path}")
