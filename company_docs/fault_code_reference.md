# FleetFix Diagnostic Trouble Code (DTC) Reference Guide

**Comprehensive OBD-II Fault Code Database**

**Last Updated:** October 2024  
**Applies To:** All FleetFix vehicles (2015+)

---

## How to Use This Guide

**Code Format:** P0XXX, P2XXX, etc.
- **P** = Powertrain
- **B** = Body
- **C** = Chassis
- **U** = Network/Communication

**First Digit After Letter:**
- **0** = Generic (SAE standard)
- **1** = Manufacturer specific
- **2** = Generic (SAE)
- **3** = Manufacturer specific

**Severity Levels:**
- 🔴 **CRITICAL** = Stop driving immediately
- 🟠 **HIGH** = Service within 24-48 hours
- 🟡 **MEDIUM** = Service within 1-2 weeks
- 🟢 **LOW** = Service at next maintenance interval

---

## Critical Powertrain Codes (Immediate Action)

### 🔴 P0300 - Random/Multiple Cylinder Misfire Detected

**Severity:** CRITICAL  
**Immediate Action:** STOP DRIVING - Risk of catalytic converter damage

**What It Means:**
Multiple engine cylinders are not firing properly. This causes rough running, loss of power, and can quickly damage your catalytic converter (very expensive repair).

**Symptoms:**
- Engine shaking/vibrating
- Loss of power
- Check engine light flashing (not steady)
- Rough idle
- Strong fuel smell
- Poor acceleration

**Common Causes:**
1. Worn or fouled spark plugs (40% of cases)
2. Faulty ignition coils (30%)
3. Vacuum leaks (15%)
4. Low fuel pressure (10%)
5. Internal engine problems (5%)

**Diagnostic Steps:**
1. Stop vehicle immediately
2. Call dispatch for tow
3. DO NOT attempt to drive to service center
4. Technician will:
   - Pull codes from all cylinders
   - Inspect spark plugs and coils
   - Check compression
   - Perform smoke test for vacuum leaks

**Estimated Repair Time:** 2-8 hours  
**Estimated Cost:** $200-$1,500+  
**Downtime:** 1-2 days

**Prevention:**
- Replace spark plugs per schedule (30K miles)
- Use quality fuel (TOP TIER rated)
- Don't ignore check engine lights
- Maintain air filter

**Related Codes:**
- P0301-P0312 (specific cylinder misfires)
- P0420/P0430 (may trigger if driven too long with misfire)

---

### 🔴 P0601 - Internal Control Module Memory Check Sum Error

**Severity:** CRITICAL  
**Immediate Action:** Do not drive, may stall without warning

**What It Means:**
The engine computer (ECM/PCM) has detected corrupted data in its memory. This is the brain of your vehicle malfunctioning.

**Symptoms:**
- Multiple warning lights
- Engine may stall
- Hard starting or no start
- Erratic engine behavior
- Transmission issues

**Common Causes:**
1. Failed ECM/PCM (60%)
2. Low battery voltage during software update (20%)
3. Water damage to computer (15%)
4. Wiring issues (5%)

**Diagnostic Steps:**
1. Tow vehicle to service center
2. Technician will:
   - Test ECM power and ground
   - Check for water damage
   - Attempt ECM reflash
   - Replace ECM if necessary

**Estimated Repair Time:** 2-4 hours  
**Estimated Cost:** $200-$1,800  
**Downtime:** 1-3 days (if ECM needs ordering)

**Prevention:**
- Keep battery in good condition
- Protect ECM from water intrusion
- Only use qualified technicians for software updates

---

### 🔴 P0700 - Transmission Control System Malfunction

**Severity:** CRITICAL  
**Immediate Action:** Stop driving if transmission slipping or not shifting

**What It Means:**
The transmission computer has detected a problem. This is a generic code that indicates more specific transmission codes are present.

**Symptoms:**
- Transmission not shifting properly
- Stuck in one gear (limp mode)
- Harsh or delayed shifts
- Slipping between gears
- Transmission warning light

**Common Causes:**
1. Low transmission fluid (30%)
2. Faulty shift solenoid (25%)
3. Wiring issues (20%)
4. Internal transmission problems (15%)
5. Transmission fluid contamination (10%)

**Diagnostic Steps:**
1. Check transmission fluid level and condition
2. If low or burnt: DO NOT drive
3. Tow to transmission specialist
4. Technician will:
   - Pull additional transmission codes
   - Inspect fluid for metal particles
   - Test shift solenoids
   - Perform pressure tests

**Estimated Repair Time:** 1-8 hours  
**Estimated Cost:** $150-$3,500+  
**Downtime:** 1 day to 1 week (major repairs)

**Prevention:**
- Change transmission fluid per schedule (30K-60K)
- Use correct fluid type (very important!)
- Don't tow beyond vehicle capacity
- Address shifting issues immediately

---

## High Priority Codes (Service Soon)

### 🟠 P0171 - System Too Lean (Bank 1)

**Severity:** HIGH  
**Service Window:** 3-5 days

**What It Means:**
Engine is getting too much air or not enough fuel. The computer is trying to compensate but can't keep up.

**Symptoms:**
- Rough idle
- Hesitation on acceleration
- Reduced fuel economy
- Engine may feel weak
- Sometimes no symptoms except check engine light

**Common Causes:**
1. Vacuum leak (intake manifold, hoses) - 40%
2. Dirty/faulty MAF sensor - 25%
3. Weak fuel pump - 15%
4. Clogged fuel filter - 10%
5. Exhaust leak before O2 sensor - 10%

**Diagnostic Steps:**
1. Visual inspection of vacuum lines
2. MAF sensor cleaning
3. Fuel pressure test
4. Smoke test for vacuum leaks

**Quick Fix Attempt:**
- Clean MAF sensor with MAF cleaner
- Check all vacuum hoses for cracks
- Clear code and test drive

**Estimated Repair Time:** 1-3 hours  
**Estimated Cost:** $150-$600  
**Downtime:** Few hours

**Can You Keep Driving?**
Yes, but:
- Fuel economy will be poor
- May damage catalytic converter over time
- Engine performance reduced
- Get diagnosed within a week

---

### 🟠 P0420 - Catalyst System Efficiency Below Threshold (Bank 1)

**Severity:** HIGH  
**Service Window:** 1-2 weeks

**What It Means:**
Your catalytic converter isn't cleaning exhaust gases as efficiently as it should. This usually means it's wearing out, but can have other causes.

**Symptoms:**
- Usually no symptoms except check engine light
- May notice reduced fuel economy
- May fail emissions test
- Possible rotten egg smell

**Common Causes:**
1. Worn out catalytic converter (50%)
2. Faulty oxygen sensor (25%)
3. Engine running rich or lean (15%)
4. Exhaust leak (10%)

**Diagnostic Steps:**
1. Check for other codes first (often secondary to other issues)
2. Test oxygen sensor readings
3. Check for exhaust leaks
4. Inspect catalytic converter for physical damage

**Money-Saving Tip:**
- Try 2-3 tanks of premium fuel first
- Sometimes carbon buildup causes false triggers
- If code returns after fuel treatment, likely hardware failure

**Estimated Repair Time:** 2-4 hours  
**Estimated Cost:** $400-$1,800  
**Downtime:** Half day

**Can You Keep Driving?**
Yes, but:
- Will fail emissions inspection
- Fuel economy may be affected
- Address within 2-3 weeks
- Don't ignore - may worsen other engine issues

---

### 🟠 P0456 - EVAP System Small Leak Detected

**Severity:** MEDIUM-HIGH  
**Service Window:** 1-2 weeks

**What It Means:**
There's a small leak in your fuel vapor recovery system (EVAP). This allows fuel vapors to escape instead of being burned in the engine.

**Symptoms:**
- Check engine light
- Possible fuel smell
- Usually no performance issues
- Will fail emissions test

**Common Causes:**
1. Loose gas cap (60% of cases!)
2. Cracked EVAP hose (20%)
3. Faulty purge valve (10%)
4. Leak in charcoal canister (10%)

**Quick Fix - Try This First:**
1. Check gas cap - tighten until 3 clicks
2. Inspect gas cap seal for cracks
3. Clear code with scanner
4. Drive 50+ miles
5. If code returns, needs repair

**Diagnostic Steps:**
1. Replace gas cap ($15-25) - try this first
2. If returns: smoke test of EVAP system
3. Pressure test to locate leak

**Estimated Repair Time:** 30 min - 2 hours  
**Estimated Cost:** $20-$400  
**Downtime:** Few hours

**Can You Keep Driving?**
Yes:
- No safety risk
- Minor environmental impact
- Address before emissions inspection

---

## Medium Priority Codes (Scheduled Service)

### 🟡 P0128 - Coolant Thermostat (Below Regulation Temperature)

**Severity:** MEDIUM  
**Service Window:** 2-4 weeks

**What It Means:**
Engine is taking too long to reach operating temperature, usually because the thermostat is stuck open.

**Symptoms:**
- Slow warm-up
- Poor heater performance in winter
- Slightly reduced fuel economy (5-10%)
- Temperature gauge stays lower than normal

**Common Causes:**
1. Stuck-open thermostat (80%)
2. Faulty coolant temperature sensor (15%)
3. Low coolant level (5%)

**Diagnostic Steps:**
1. Check coolant level
2. Monitor temperature gauge behavior
3. Test coolant temperature sensor
4. Replace thermostat

**Estimated Repair Time:** 1-2 hours  
**Estimated Cost:** $150-$350  
**Downtime:** Few hours

**Impact If Ignored:**
- 5-10% reduction in fuel economy
- Increased emissions
- Increased engine wear
- Poor cabin heating

**Can You Keep Driving?**
Yes:
- No immediate danger
- Schedule within a month
- Winter driving will be uncomfortable

---

### 🟡 P0401 - Exhaust Gas Recirculation (EGR) Flow Insufficient

**Severity:** MEDIUM  
**Service Window:** 2-4 weeks

**What It Means:**
The EGR system isn't recirculating exhaust gases properly. This increases emissions and can cause performance issues.

**Symptoms:**
- Check engine light
- Rough idle
- Hesitation on acceleration
- Failed emissions test
- Sometimes no symptoms

**Common Causes:**
1. Clogged EGR valve (50%)
2. Clogged EGR passages (30%)
3. Faulty EGR valve (15%)
4. Wiring issues (5%)

**Diagnostic Steps:**
1. Inspect EGR valve for carbon buildup
2. Clean EGR passages
3. Test EGR valve operation
4. Replace if necessary

**Estimated Repair Time:** 1-3 hours  
**Estimated Cost:** $200-$500  
**Downtime:** Few hours

**Can You Keep Driving?**
Yes:
- No immediate safety risk
- May notice performance issues
- Will fail emissions test
- Schedule within 4 weeks

---

### 🟡 P0442 - EVAP System Leak Detected (Small)

**Severity:** LOW-MEDIUM  
**Service Window:** 1-2 months

**What It Means:**
Similar to P0456 but even smaller leak. Very minor fuel vapor leak.

**Quick Fix:**
- Same as P0456 - check gas cap first
- 70% of the time it's just the gas cap

**Estimated Cost:** $20-$300  
**Can You Keep Driving?** Yes, non-urgent

---

## Low Priority Codes (Next Scheduled Maintenance)

### 🟢 P0135 - O2 Sensor Heater Circuit (Bank 1, Sensor 1)

**Severity:** LOW  
**Service Window:** Next scheduled maintenance

**What It Means:**
The heating element in your oxygen sensor isn't working. The sensor still works but takes longer to activate.

**Symptoms:**
- Check engine light
- Slightly reduced fuel economy during warm-up
- No other symptoms

**Common Causes:**
1. Failed O2 sensor (60%)
2. Wiring issues (30%)
3. Blown fuse (10%)

**Estimated Repair Time:** 30 min - 1 hour  
**Estimated Cost:** $150-$350  

**Can You Keep Driving?**
Yes:
- Very low impact
- Minor fuel economy effect
- Fix at next service visit

---

### 🟢 P0506 - Idle Control System RPM Lower Than Expected

**Severity:** LOW  
**Service Window:** Next scheduled maintenance

**What It Means:**
Engine idle speed is lower than the computer wants it to be. Usually causes rough idle.

**Symptoms:**
- Rough idle
- Stalling when coming to stop
- Check engine light

**Common Causes:**
1. Dirty throttle body (60%)
2. Vacuum leak (20%)
3. Faulty idle air control valve (20%)

**Quick Fix:**
- Clean throttle body
- Often resolves issue

**Estimated Cost:** $100-$300  
**Can You Keep Driving?** Yes, just annoying

---

## Body & Chassis Codes

### B1000-B1999: Body Codes

**Common Body Codes:**
- **B1318** - Battery Voltage Low: Check battery and alternator
- **B1342** - ECU Voltage Low: Electrical system issue
- **B1681** - HVAC Blend Door: Climate control issue

**Severity:** Usually LOW - address at next service

---

### C0000-C0999: Chassis Codes (ABS/Stability Control)

**Common Chassis Codes:**
- **C0035** - Left Front Wheel Speed Sensor: ABS sensor issue
- **C1201** - Engine Control System Malfunction: Communication issue
- **C1288** - Brake Lamp Switch Circuit: Brake light switch problem

**Most chassis codes affect ABS/traction control:**
- Vehicle still drivable
- May not have ABS assistance
- Schedule service within 1 week

---

## Network/Communication Codes

### U0000-U0999: Network Codes

**Common Network Codes:**
- **U0073** - CAN Bus Off: Communication failure
- **U0100** - Lost Communication with ECM: Computer communication issue
- **U0101** - Lost Communication with TCM: Transmission communication issue

**Severity:** Usually HIGH - affects multiple systems  
**Action:** Service within 24-48 hours

---

## Multiple Codes - What Do They Mean?

### Cascade Failures

Often one problem triggers multiple codes. Here are common patterns:

**Pattern 1: Misfire Cascade**
- P0300 (Random Misfire)
- P0301-P0304 (Specific cylinder misfires)
- P0420 (Catalyst efficiency)
- **Root Cause:** Usually ignition system - fix misfire first

**Pattern 2: Lean/Rich Cascade**
- P0171 (System Lean Bank 1)
- P0174 (System Lean Bank 2)
- P0420/P0430 (Catalyst efficiency both banks)
- **Root Cause:** Usually MAF sensor or vacuum leak

**Pattern 3: EVAP System Multiple**
- P0442 (Small leak)
- P0455 (Large leak)
- P0457 (Loose gas cap)
- **Root Cause:** Start with gas cap, then EVAP system

**Pro Tip:** Always address the lowest-numbered code first - it's usually the root cause.

---

## Code Clearing Guidelines

### When Can Codes Be Cleared?

**OK to Clear:**
- After confirmed repair
- After gas cap tightened (P0455/P0456/P0457)
- False triggers (rare)

**DO NOT Clear Without Repair:**
- Safety-related codes
- Emissions codes before testing
- Codes needed for warranty claims
- Recurring codes

### How Codes Clear Naturally

**Drive Cycle:**
Most codes clear after 40-80 "warm-up cycles" if the problem is fixed:
- Start engine cold
- Drive until engine reaches operating temperature
- Includes various driving conditions (idle, cruise, acceleration)

**Continuous Monitors:**
Some systems check every second:
- Misfire detection
- Fuel system
- Comprehensive component monitoring

**Non-Continuous Monitors:**
These run under specific conditions:
- Catalyst monitoring
- EVAP system
- EGR system
- Oxygen sensors

---

## Fleet-Specific Code Tracking

### High-Frequency Codes in Our Fleet

**Top 5 Codes (Last 12 Months):**

1. **P0455** - EVAP Large Leak (mostly gas caps) - 23% of all codes
2. **P0128** - Thermostat Below Temp - 15% of codes
3. **P0171** - System Lean Bank 1 - 12% of codes
4. **P0420** - Catalyst Efficiency - 11% of codes
5. **P0300** - Random Misfire - 8% of codes

### Cost Impact

**Average repair cost by code category:**
- EVAP codes (P04XX): $75 average
- Oxygen sensor codes (P013X): $225 average
- Catalyst codes (P042X): $950 average
- Misfire codes (P030X): $385 average
- Transmission codes (P07XX): $1,850 average

---

## Preventive Actions to Avoid Codes

### Top 10 Prevention Tips

1. **Always tighten gas cap** until it clicks 3 times
2. **Use TOP TIER fuel** - reduces carbon buildup
3. **Replace spark plugs on schedule** - prevents misfires
4. **Keep up with oil changes** - prevents many engine codes
5. **Don't ignore check engine lights** - small problems become big ones
6. **Check tire pressure weekly** - prevents TPMS codes
7. **Address fluid leaks immediately** - prevents major failures
8. **Clean MAF sensor annually** - prevents lean/rich codes
9. **Replace air filter regularly** - prevents O2 sensor fouling
10. **Park indoors when possible** - protects electrical systems

---

## Quick Reference Decision Tree

```
Check Engine Light ON
↓
Is it FLASHING?
├─ YES → STOP DRIVING - Call for tow (P0300 likely)
└─ NO → Continue
    ↓
    Any unusual symptoms?
    ├─ Loss of power, rough running → Service within 24hrs
    ├─ Transmission issues → Service within 24hrs
    ├─ Fuel smell → Check gas cap, then service
    ├─ No symptoms → Get diagnosed within 1 week
    └─ Just light, no issues → Schedule at convenience (still within 2 weeks)
```

---

## When to Call Dispatch Immediately

**CALL NOW if you see:**
- Flashing check engine light
- Multiple warning lights at once
- Loss of power/acceleration
- Unusual sounds with check engine light
- Smoke from engine
- Fluid actively leaking
- Transmission slipping/not shifting

**Can Wait for Scheduled Service:**
- Steady check engine light, no symptoms
- EVAP codes (after checking gas cap)
- Single warning light, vehicle driving normally

---

## Appendix: Code Number Ranges

**P0XXX Codes:**
- P00XX-P01XX: Fuel and air metering
- P02XX: Injector circuit
- P03XX: Ignition system
- P04XX: Emissions control
- P05XX: Idle control
- P06XX: Computer output circuits
- P07XX: Transmission

**P2XXX Codes:**
- P20XX-P21XX: Fuel and air metering
- P22XX-P23XX: Fuel and air metering
- P24XX-P26XX: Emissions control
- P27XX-P28XX: Emissions control

---

**For code diagnosis or questions:**  
Fleet Maintenance Hotline: 816-555-FLEET (3533)  
Available: M-F 7am-7pm, Sat 8am-4pm

**Emergency After-Hours:**  
816-555-9999 (for critical issues only)

---

*This reference guide is for informational purposes. Always have codes professionally diagnosed. Do not attempt repairs beyond your skill level.*