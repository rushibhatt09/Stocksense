# StockSense - Documentation Index

This document is your guide to all StockSense documentation. Start here to understand which documents to read.

---

## 📚 Documentation Files

### 1. **PROJECT.md** - Start Here! 📌
**Purpose**: High-level project overview aligned with the problem statement

**Content**:
- Problem statement & user target
- Feature overview (7 major areas)
- Navigation structure
- Technical architecture (append-only ledger)
- Example end-to-end workflows
- Business rules & success metrics
- Current status & deployment info

**Read this if**: You want to understand **what** the system does and **why**.

**Time to read**: 15-20 minutes

---

### 2. **CLAUDE.md** - Technical Deep Dive 🏗️
**Purpose**: Complete technical documentation for developers

**Content**:
- Project architecture & philosophy
- Complete database schema with all tables & relationships
- API routes documentation
- Frontend structure & components
- Authentication & security details
- Implementation patterns & code examples
- Development setup instructions
- Configuration reference
- Testing strategy
- Multi-agent development strategy

**Read this if**: You need technical details for implementation.

**Time to read**: 30-40 minutes (skim first, bookmark for reference)

---

### 3. **AGENTS.md** - Multi-Agent Architecture 🤖
**Purpose**: Define 4 specialized agents and their roles

**Content**:
- **Agent 1: UI Agent** (React components & pages)
- **Agent 2: Auth/Guard Agent** (Authentication & authorization)
- **Agent 3: Inventory Agent** (Products, warehouses, locations)
- **Agent 4: Operations Agent** (Documents, stock moves, ledger)

Each agent includes:
- Clear responsibilities & deliverables
- Owned files & directories
- API endpoints (owned & consumed)
- Database models to build/enhance
- Business logic & validation rules
- Output files checklist
- Dependencies on other agents

**Also includes**:
- Dependency graph showing order of development
- Cross-agent communication contracts (JSON schemas)
- Testing strategy
- Handoff checklists
- Success criteria

**Read this if**: You're an agent needing to understand your role & scope.

**Time to read**: 20-30 minutes (or 5-10 minutes for your specific agent)

---

### 4. **ONBOARDING.md** - Agent Getting Started Guide 🚀
**Purpose**: Step-by-step setup & first tasks for each agent

**Content**:
- Shared prerequisites & setup (for all agents)
- Agent 1 (UI): Dashboard building, component library, React Query patterns
- Agent 2 (Auth): Guard decorators, OTP service, rate limiting
- Agent 3 (Inventory): API schemas, routes, stock calculation
- Agent 4 (Operations): Document lifecycle, validation logic, stock moves

Each agent's section includes:
- Essential files to read first
- Your first task (concrete, actionable)
- Code examples & patterns
- Expected API endpoints
- Testing instructions
- Checklist

**Also includes**:
- Common patterns (error handling, timestamps, DB queries)
- Useful bash/npm commands
- Important notes (transactions, timezones, error exposure)
- Getting help resources

**Read this if**: You're starting work and need concrete next steps.

**Time to read**: 10-15 minutes for your agent + 5-10 for common patterns

---

### 5. **README.md** - Project Repository Overview
**Purpose**: Quick start guide for running the system

**Content**:
- Core idea (append-only ledger)
- How to run backend & frontend
- Demo accounts
- Repository layout

**Read this if**: You just cloned the repo and want to get it running.

**Time to read**: 5 minutes

---

## 🎯 Quick Navigation by Role

### If you're the **UI Agent** (Frontend)
1. Read: **PROJECT.md** (understand features)
2. Skim: **CLAUDE.md** → "Frontend Structure" section
3. Read: **AGENTS.md** → "Agent 1: UI Agent" section
4. Read: **ONBOARDING.md** → "Agent 1: UI Agent - Getting Started" section
5. Bookmark: **CLAUDE.md** for API reference

---

### If you're the **Auth/Guard Agent** (Auth & Security)
1. Read: **CLAUDE.md** → "Authentication & Security" section
2. Skim: **PROJECT.md** → "Authentication & Access Control" section
3. Read: **AGENTS.md** → "Agent 2: Auth/Guard Agent" section
4. Read: **ONBOARDING.md** → "Agent 2: Auth/Guard Agent - Getting Started" section
5. Study: Existing code in `backend/app/api/routes/auth.py`

---

### If you're the **Inventory Agent** (Products & Stock)
1. Read: **PROJECT.md** → "Product Management" & "Settings"
2. Read: **CLAUDE.md** → "Database Schema → Inventory & Stock"
3. Read: **AGENTS.md** → "Agent 3: Inventory Agent" section
4. Read: **ONBOARDING.md** → "Agent 3: Inventory Agent - Getting Started" section
5. Understand: Stock calculation logic in AGENTS.md

---

### If you're the **Operations Agent** (Documents & Ledger)
1. Read: **PROJECT.md** → "Core Operations" & "Example Flow: End-to-End"
2. Read: **CLAUDE.md** → "Database Schema → Operations & Stock Ledger" & "Ledger-Based Inventory"
3. Read: **AGENTS.md** → "Agent 4: Operations Agent" section
4. Read: **ONBOARDING.md** → "Agent 4: Operations Agent - Getting Started" section
5. Study: Append-only ledger pattern thoroughly

---

### If you're a **Product Manager** or **Stakeholder**
1. Read: **PROJECT.md** (full overview)
2. Check: Current Status & Next Steps in CLAUDE.md
3. Reference: Success Metrics in PROJECT.md

---

### If you're **Setting Up CI/CD** or **DevOps**
1. Read: **CLAUDE.md** → "Development Setup" & "Deployment"
2. Check: Backend requirements in `backend/requirements.txt`
3. Check: Frontend setup in `frontend/package.json`
4. Reference: `docker-compose.yml` for database setup

---

## 📊 Documentation Summary Table

| Document | Purpose | Length | Audience | Read First? |
|----------|---------|--------|----------|------------|
| PROJECT.md | Feature overview | 20 min | Everyone | ✅ YES |
| CLAUDE.md | Technical reference | 40 min | Developers | ✅ YES (skim) |
| AGENTS.md | Agent architecture | 30 min | Each agent | ✅ YES (your section) |
| ONBOARDING.md | Getting started | 15 min | Each agent | ✅ YES (immediately) |
| DOCUMENTATION.md | This file | 10 min | New readers | ✅ (you're reading it!) |
| README.md | Quick start | 5 min | New readers | ✅ (quick ref) |
| CLAUDE.md (ref) | Code patterns | 20 min | During development | 📌 Bookmark |

---

## 🔄 Recommended Reading Order for New Team Members

### Day 1: Understanding the System
1. **README.md** (5 min) – Get the basics
2. **PROJECT.md** (20 min) – Understand what we're building
3. **CLAUDE.md** → Skim (10 min) – Architecture overview
4. Set up backend & frontend locally (30 min)
5. Test with demo accounts (10 min)

**Total: ~75 minutes**

### Day 2: Understanding Your Role
1. **AGENTS.md** → Your agent section (20 min)
2. **ONBOARDING.md** → Your agent section (15 min)
3. Review existing code in your domain (30 min)
4. Run your first task (60 min)
5. Push a small PR with your work (30 min)

**Total: ~2.5 hours**

### Ongoing: Reference & Deep Dives
- **CLAUDE.md** – Bookmark for API & schema reference
- **AGENTS.md** → Dependency sections to understand what other agents provide
- **ONBOARDING.md** → Common tasks & patterns section

---

## 🔑 Key Concepts to Understand

### 1. **Append-Only Ledger** (Critical!)
- Stock moves are **never updated or deleted**
- All stock quantities are **derived** from summing moves
- Mistakes corrected by creating **opposite moves**
- Ensures 100% audit trail with zero data loss

**Learn more**: PROJECT.md → "Single Source of Truth", CLAUDE.md → "Ledger-Based Inventory"

### 2. **4-Agent Architecture**
- Each agent owns a domain (UI, Auth, Inventory, Operations)
- Clear dependencies (Auth → Inventory → Operations, all consume Auth)
- Agents build APIs consumed by UI

**Learn more**: AGENTS.md → Overview, Dependency Graph

### 3. **Document Workflow**
- Documents progress: Draft → Waiting → Ready → Done (or Canceled)
- Validation creates stock moves and locks document
- Never edit validated documents; create adjustments instead

**Learn more**: AGENTS.md → Agent 4, PROJECT.md → Example Flow

### 4. **Virtual vs. Physical Locations**
- **Physical**: Real warehouse/shelf locations where stock sits
- **Virtual**: Vendor, Customer, Adjustment, Scrap (explain where stock came from/went)

**Learn more**: CLAUDE.md → Location Types, PROJECT.md → Move History

---

## 🔗 Cross-References

### Understanding Stock Calculations
- **Concept**: CLAUDE.md → Ledger-Based Inventory
- **Implementation**: AGENTS.md → Inventory Agent → Business Logic
- **Example**: PROJECT.md → Example Flow: End-to-End

### Building an API Endpoint
- **Patterns**: CLAUDE.md → Important Patterns
- **Example**: AGENTS.md → [Your Agent] → API Endpoints
- **Step-by-step**: ONBOARDING.md → [Your Agent] → Your First Task

### Testing Your Work
- **Strategy**: AGENTS.md → Testing Strategy
- **Commands**: ONBOARDING.md → Useful Commands
- **Examples**: CLAUDE.md → Testing section

---

## 📋 Documentation Maintenance

These documents are **living documentation** and should be updated as the project evolves:

- **After completing an agent**: Update AGENTS.md → Handoff Checklist
- **After adding a feature**: Update PROJECT.md & CLAUDE.md
- **After deploying**: Update CLAUDE.md → Current Status
- **After changing architecture**: Update AGENTS.md & CLAUDE.md

---

## 🆘 Still Have Questions?

1. **"How do I build an API endpoint?"**
   → ONBOARDING.md → Your Agent → Your First Task

2. **"What's the database schema?"**
   → CLAUDE.md → Database Schema

3. **"What APIs does the UI consume?"**
   → AGENTS.md → Agent 1 → API Consumption

4. **"How does the stock ledger work?"**
   → CLAUDE.md → Ledger-Based Inventory + PROJECT.md → Single Source of Truth

5. **"What's my agent responsible for?"**
   → AGENTS.md → [Your Agent] → Responsibilities

6. **"How do I know when I'm done?"**
   → AGENTS.md → [Your Agent] → Output Files + Success Criteria

7. **"What's the next agent's dependency?"**
   → AGENTS.md → Dependency Graph

---

## 📞 Quick Links

- **API Documentation** (when running): http://localhost:8000/docs
- **Frontend Dev Server**: http://localhost:5173
- **Database Schema**: CLAUDE.md → Database Schema
- **All API Routes**: CLAUDE.md → API Routes
- **Git Repository**: `git log --oneline` to see commits

---

**Last Updated**: 2026-09-26  
**Project**: StockSense Inventory Management System  
**Status**: Core architecture documented, ready for 4-agent development

---

## 📚 Document Statistics

| Document | Type | Size | Focus |
|----------|------|------|-------|
| PROJECT.md | Feature Spec | ~400 lines | What & Why |
| CLAUDE.md | Technical Ref | ~500 lines | Architecture & How |
| AGENTS.md | Team Guide | ~600 lines | Roles & Boundaries |
| ONBOARDING.md | Quickstart | ~700 lines | First Steps |
| DOCUMENTATION.md | Index | ~300 lines | Navigation |
| **Total** | | **2,500+ lines** | **Complete reference** |

---

**🎉 You now have everything you need to start building StockSense!**

Pick your document above and dive in. Happy coding! 🚀
