# Definition of Done
# Every item below must hold before any story is marked Done. The gate runner
# executes each command literally and records command, exit code, output tail,
# and commit SHA into sprint-current.yaml. Nonzero exit = not Done, no exceptions.

## Commands (replace with the project's actual commands at inception)
- [ ] Tests pass: `npm test` → exit 0
- [ ] Lint clean: `npx eslint .` → exit 0
- [ ] Build succeeds: `npm run build` → exit 0

## Standing rules (mechanically checked where possible)
- [ ] Every acceptance criterion has at least one test exercising it
- [ ] Forward blast radius resolved: `tier: map` wiki articles whose code_refs
      overlap this story's diff are updated or re-verified within the story, and
      `yt_wiki.py sweep` is CLEAN when run AFTER the story's last commit
- [ ] If the story changed build/test/run commands, stack, or architecture:
      CLAUDE.md updated in the same commit
- [ ] If the story deleted code: the reason is recorded in the story file History
