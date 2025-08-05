# NTN Stack Events Architecture Cleanup Checklist

## Executive Summary
Complete analysis of A4, D1, D2, T1 events across frontend and backend. Found extensive duplication and architectural chaos requiring full cleanup and rebuild.

## =¨ Critical Issues Found
- **47+ Event-related files** across frontend/backend
- **Multiple 1000+ line components** with duplicate functionality  
- **Inconsistent API usage** between NetStack and SimWorld
- **Orphaned files and references** scattered throughout codebase

---

## =Ê A4 Event Files (11 files)

### =Ñ Frontend A4 Files to DELETE
- [ ] `simworld/frontend/src/components/domains/measurement/viewers/EnhancedA4Viewer.tsx` (Enhanced viewer - not used in routes)
- [ ] `simworld/frontend/src/components/domains/measurement/charts/EnhancedA4Viewer.tsx` (1069 lines - duplicate implementation)
- [ ] `simworld/frontend/src/components/domains/measurement/charts/EnhancedA4Chart.tsx` (1103 lines - duplicate implementation)
- [ ] `simworld/frontend/src/components/domains/measurement/charts/EventA4Viewer.tsx` (1233 lines - oversized component)
- [ ] `simworld/frontend/src/components/domains/measurement/charts/EventA4Chart.tsx` (Basic wrapper)
- [ ] `simworld/frontend/src/components/domains/measurement/charts/EventA4Viewer.scss`
- [ ] `simworld/frontend/src/components/domains/measurement/charts/EventA4Chart.scss`
- [ ] `simworld/frontend/src/components/domains/measurement/charts/EnhancedA4Viewer.scss`

### =' A4 Supporting Files to DELETE
- [ ] `simworld/frontend/src/components/domains/measurement/shared/hooks/useEventA4Logic.ts`
- [ ] `simworld/frontend/src/components/domains/measurement/shared/components/A4EventSpecificChart.tsx`

### =Ä A4 Documentation
- [ ] `doc/images/Event-A4.jpg` (Keep - documentation image)

---

## =Ê D2 Event Files (25+ files)

### =Ñ Frontend D2 Files to DELETE

#### Core D2 Components (Oversized/Duplicate)
- [ ] `simworld/frontend/src/components/domains/measurement/charts/PureD2Chart.tsx` (2426 lines - **CRITICAL OVERSIZED**)
- [ ] `simworld/frontend/src/components/domains/measurement/charts/EventD2Viewer.tsx` (Main viewer used by /d2-dashboard route)
- [ ] `simworld/frontend/src/components/domains/measurement/charts/EnhancedD2Chart.tsx` (842 lines - duplicate)
- [ ] `simworld/frontend/src/components/domains/measurement/charts/EnhancedD2Viewer.tsx` (621 lines - unused enhanced viewer)
- [ ] `simworld/frontend/src/components/domains/measurement/charts/EventD2Chart.tsx` (52 lines - basic wrapper)

#### D2 Backup and Alternative Implementations
- [ ] `simworld/frontend/src/components/domains/measurement/charts/EventD2Viewer_Original_Backup.tsx` (Backup file)
- [ ] `simworld/frontend/src/components/charts/EnhancedRealD2Chart.tsx` (842 lines - duplicate of EnhancedD2Chart)

#### D2 Sub-components Directory
- [ ] `simworld/frontend/src/components/domains/measurement/charts/d2-components/D2NarrationPanel.tsx`
- [ ] `simworld/frontend/src/components/domains/measurement/charts/d2-components/D2AnimationController.tsx`
- [ ] `simworld/frontend/src/components/domains/measurement/charts/d2-components/D2ThemeManager.ts`
- [ ] `simworld/frontend/src/components/domains/measurement/charts/d2-components/D2DataManager.tsx`
- [ ] `simworld/frontend/src/components/domains/measurement/charts/d2-components/README.md`

#### D2 Style Files
- [ ] `simworld/frontend/src/components/domains/measurement/charts/EventD2Viewer.scss`
- [ ] `simworld/frontend/src/components/domains/measurement/charts/EventD2Chart.scss`
- [ ] `simworld/frontend/src/components/domains/measurement/charts/EnhancedD2Viewer.scss`

#### D2 Services and Hooks
- [ ] `simworld/frontend/src/services/unifiedD2DataService.ts`
- [ ] `simworld/frontend/src/services/improvedD2DataService.ts`
- [ ] `simworld/frontend/src/services/realD2DataService.ts`
- [ ] `simworld/frontend/src/hooks/useD2EventData.ts`
- [ ] `simworld/frontend/src/components/domains/measurement/shared/hooks/useEventD2Logic.ts`
- [ ] `simworld/frontend/src/components/domains/measurement/shared/components/D2EventSpecificChart.tsx`

#### D2 Pages and Demo Files
- [ ] `simworld/frontend/src/pages/ImprovedD2Demo.tsx`

### =Ä D2 Documentation to DELETE
- [ ] `simworld/frontend/D2_API_ENDPOINT_FIXES_COMPLETE_REPORT.md`
- [ ] `simworld/frontend/D2_USER_FEEDBACK_FIXES_REPORT.md`
- [ ] `simworld/frontend/D2_LAYOUT_AND_DATA_FIXES_REPORT.md`
- [ ] `simworld/frontend/D2_API_FALLBACK_REPORT.md`

### =Ä Backend D2 Files to DELETE
- [ ] `simworld/backend/app/api/d2_event_endpoints.py` (94 lines - duplicate API)
- [ ] `simworld/backend_backup_20250805_0020/app/api/d2_event_endpoints.py` (Backup file)

---

## =Ê D1 Event Files (1 file)

### =Ñ D1 Files to DELETE
- [ ] `simworld/frontend/src/components/domains/measurement/charts/EventD1Chart.scss` (Orphaned style file)

---

## =Ê T1 Event Files (1 file)

### =Ñ T1 Files to DELETE
- [ ] `simworld/frontend/src/components/domains/measurement/charts/EnhancedT1Viewer.scss` (Orphaned style file)

---

## =Ä Backend Measurement Event Files

### =Ñ NetStack Backend Files to DELETE
- [ ] `netstack/netstack_api/routers/measurement_events_router_simple.py` (Duplicate simplified router)

### =' NetStack Backend Files to REVIEW/REFACTOR
- [ ] `netstack/netstack_api/routers/measurement_events_router.py` (760 lines - comprehensive router)
- [ ] `netstack/netstack_api/services/measurement_event_service.py` (Core measurement service)
- [ ] `netstack/netstack_api/services/handover_measurement_service.py` (Handover measurement service)
- [ ] `netstack/netstack_api/services/event_bus_service.py` (Event bus service)
- [ ] `netstack/src/services/research/threegpp_event_generator.py` (3GPP event generator)

---

## =' Shared/Infrastructure Files

### =Ñ Frontend Shared Files to DELETE (Event-specific)
- [ ] `simworld/frontend/src/components/layout/MeasurementEventsModal.tsx` (Contains hardcoded Event references)
- [ ] `simworld/frontend/src/components/layout/MeasurementEventsModal.scss`
- [ ] `simworld/frontend/src/components/domains/measurement/components/EventSelector.tsx`
- [ ] `simworld/frontend/src/components/domains/measurement/components/EventSelector.scss`
- [ ] `simworld/frontend/src/components/domains/measurement/components/EventConfigPanel.tsx`
- [ ] `simworld/frontend/src/components/domains/measurement/components/EventConfigPanel.scss`
- [ ] `simworld/frontend/src/components/domains/measurement/MeasurementEventDashboard.tsx`

### =' Frontend Configuration Files to REVIEW
- [ ] `simworld/frontend/src/config/measurement-api-config.ts` (API configuration)
- [ ] `simworld/frontend/src/types/measurement-view-modes.ts` (Type definitions)
- [ ] `simworld/frontend/src/components/domains/measurement/config/eventConfig.ts` (Event configuration)

### =Ñ Education/Support Files to DELETE
- [ ] `simworld/frontend/src/components/domains/measurement/education/ConceptExplanation.tsx`
- [ ] `simworld/frontend/src/components/domains/measurement/education/InteractiveGuide.tsx`

### =Ñ Shared Components Directory to DELETE
- [ ] `simworld/frontend/src/components/domains/measurement/shared/` (Entire directory - 20+ files)

### =Ñ Adapters and Generic Components to DELETE
- [ ] `simworld/frontend/src/components/domains/measurement/adapters/EnhancedViewerAdapter.tsx`
- [ ] `simworld/frontend/src/components/common/EnhancedParameterPanel.tsx`

---

## >ê Test Files

### =' Test Files to REVIEW/UPDATE
- [ ] `simworld/frontend/src/test/phase1.5-integration-test.tsx` (Contains Event references)
- [ ] `simworld/frontend/src/test/e2e.test.tsx` (Contains Event references)
- [ ] `simworld/frontend/src/test/components.test.tsx` (Contains Event references)

---

## =ñ Route Dependencies

### =' Main Route File to UPDATE
- [ ] `simworld/frontend/src/main.tsx` (Lines 217-225 - /d2-dashboard route)

---

## =Ê Summary Statistics

### Files by Category
- **A4 Event Files**: 11 files (mostly 1000+ lines each)
- **D2 Event Files**: 25+ files (including 2426-line monster)
- **D1 Event Files**: 1 file (orphaned stylesheet)
- **T1 Event Files**: 1 file (orphaned stylesheet)
- **Backend Files**: 7 files
- **Shared/Infrastructure**: 20+ files
- **Total Estimated**: **65+ files for deletion**

### Code Size Reduction
- **Before**: ~15,000+ lines across multiple oversized components
- **After**: ~2,000 lines in clean, modular architecture
- **Reduction**: ~85% code reduction with improved maintainability

---

##  Execution Plan

### Phase 1: Complete Cleanup (30 minutes)
1. **Backup current state**: `git checkout -b event-architecture-rebuild`
2. **Delete all marked files**: Use checklist above
3. **Remove route dependencies**: Update main.tsx routes
4. **Clear imports**: Remove imports from index.ts files

### Phase 2: Architecture Rebuild (6-8 hours)
1. **Create new unified event architecture**
2. **Implement A4 system** (using shared components)
3. **Implement D2 system** (using shared components)
4. **Update routes and integration**
5. **Test complete system**

### Phase 3: Verification (1 hour)
1. **Test all routes work**
2. **Verify no broken imports**
3. **Confirm event functionality**
4. **Performance validation**

---

## <¯ Success Criteria

- [ ] **Zero duplicate components** - One clear implementation per event type
- [ ] **File size < 200 lines** - No oversized monolithic components
- [ ] **Unified API usage** - Single API strategy across all components
- [ ] **Working /d2-dashboard route** - Trajectory display functional
- [ ] **Maintainable architecture** - Clear separation of concerns
- [ ] **Complete test coverage** - All event types tested

---

*Generated by comprehensive ultrathink analysis of NTN Stack Event architecture*
*Total files analyzed: 200+ across frontend/backend*
*Cleanup impact: 65+ files for deletion, 85% code reduction*