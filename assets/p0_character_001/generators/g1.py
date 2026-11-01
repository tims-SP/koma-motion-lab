"""View 000 (front) and View 045 (three-quarter, camera on character's right)."""
from common import *


def front_view():
    s = svg_open(640, 800, "0 0 640 800")
    s += '<g id="view-front" data-yaw="0">\n'
    # ---------- back hair mass ----------
    s += '<g id="hair-back">\n'
    s += ('  <path d="M320 104C226 104 170 176 168 274C166 350 172 432 184 504C192 550 212 582 244 588'
          'C262 591 273 577 268 558C261 530 249 500 247 466C243 416 250 328 262 286C278 226 298 192 320 188'
          'C342 192 362 226 378 286C390 328 397 416 393 466C391 500 379 530 372 558C367 577 378 591 396 588'
          'C428 582 448 550 456 504C468 432 474 350 472 274C470 176 414 104 320 104Z" '
          'fill="%s" stroke="%s" stroke-width="3.5" stroke-linejoin="round"/>\n' % (HAIR, LINE))
    s += '  <path d="M188 424C198 500 216 558 248 584C258 590 266 582 264 570C254 536 244 496 242 456Z" fill="%s" opacity=".9"/>\n' % HAIR_SH
    s += '  <path d="M452 424C442 500 424 558 392 584C382 590 374 582 376 570C386 536 396 496 398 456Z" fill="%s" opacity=".9"/>\n' % HAIR_SH
    s += '</g>\n'
    # ---------- hood behind neck ----------
    s += '<g id="hood">\n'
    s += ('  <path d="M320 556C238 556 172 596 136 656C118 684 110 714 106 744L166 744C170 700 184 662 212 636'
          'C238 610 276 594 320 594C364 594 402 610 428 636C456 662 470 700 474 744L534 744C530 714 522 684 504 656'
          'C468 596 402 556 320 556Z" fill="%s" stroke="%s" stroke-width="3.5" stroke-linejoin="round"/>\n' % (JACKET, LINE))
    s += '  <path d="M212 636C238 610 276 594 320 594C364 594 402 610 428 636" fill="none" stroke="%s" stroke-width="4.5" stroke-linecap="round"/>\n' % GOLD
    s += '</g>\n'
    # ---------- jacket body ----------
    s += '<g id="jacket">\n'
    s += ('  <path d="M320 566C246 566 186 596 146 638C114 672 96 730 88 800L552 800C544 730 526 672 494 638'
          'C454 596 394 566 320 566Z" fill="%s" stroke="%s" stroke-width="3.5" stroke-linejoin="round"/>\n' % (JACKET, LINE))
    s += '  <path d="M470 620C496 646 516 690 524 742L548 800L500 800C494 730 486 664 460 632Z" fill="%s" opacity=".85"/>\n' % JACKET_DK
    s += '</g>\n'
    # ---------- neck ----------
    s += '<g id="neck">\n'
    s += '  <path d="M286 458L284 542C284 568 356 568 356 542L354 458Z" fill="%s" stroke="%s" stroke-width="3"/>\n' % (SKIN, LINE)
    s += '  <path d="M286 458C292 508 348 508 354 458C348 496 292 496 286 458Z" fill="%s"/>\n' % SKIN_SH
    s += '</g>\n'
    # ---------- shirt ----------
    s += '<g id="shirt">\n'
    s += '  <path d="M290 596L350 596L372 800L268 800Z" fill="%s" stroke="%s" stroke-width="3"/>\n' % (SHIRT, LINE)
    s += '  <path d="M350 596L372 800L352 800L336 596Z" fill="%s"/>\n' % SHIRT_SH
    s += '  <circle cx="320" cy="712" r="4.5" fill="%s" stroke="%s" stroke-width="1.6"/>\n' % (SHIRT_SH, LINE)
    s += '</g>\n'
    # ---------- collar flaps ----------
    s += '<g id="collar">\n'
    s += '  <path d="M284 586L320 610L296 656L266 616Z" fill="%s" stroke="%s" stroke-width="3" stroke-linejoin="round"/>\n' % (SHIRT, LINE)
    s += '  <path d="M356 586L320 610L344 656L374 616Z" fill="%s" stroke="%s" stroke-width="3" stroke-linejoin="round"/>\n' % (SHIRT, LINE)
    s += '  <path d="M356 586L320 610L344 656L374 616Z" fill="%s" opacity=".55"/>\n' % SHIRT_SH
    s += '</g>\n'
    # ---------- bow tie ----------
    s += '<g id="bowtie">\n'
    s += '  <path d="M306 626C288 608 258 610 250 626C242 642 262 658 286 650C296 647 304 638 306 626Z" fill="%s" stroke="%s" stroke-width="2.6" stroke-linejoin="round"/>\n' % (BOW, LINE)
    s += '  <path d="M334 626C352 608 382 610 390 626C398 642 378 658 354 650C344 647 336 638 334 626Z" fill="%s" stroke="%s" stroke-width="2.6" stroke-linejoin="round"/>\n' % (BOW, LINE)
    s += '  <path d="M306 626C288 608 258 610 250 626C258 620 284 620 302 632Z" fill="%s" opacity=".7"/>\n' % BOW_DK
    s += '  <path d="M310 620C320 614 332 614 340 620C336 632 336 642 340 652C330 658 312 658 300 652C306 642 306 632 310 620Z" fill="%s" stroke="%s" stroke-width="2.6"/>\n' % (BOW, LINE)
    s += '  <path d="M308 652C300 676 298 700 304 722C314 706 320 690 320 668Z" fill="%s" stroke="%s" stroke-width="2.4"/>\n' % (BOW, LINE)
    s += '  <path d="M332 652C342 674 344 696 338 716C328 702 324 686 324 668Z" fill="%s" stroke="%s" stroke-width="2.4"/>\n' % (BOW_DK, LINE)
    s += '</g>\n'
    # ---------- jacket front edges over shirt ----------
    s += '<g id="jacket-front">\n'
    s += '  <path d="M268 600C252 640 244 700 242 800L288 800C286 720 284 656 296 604Z" fill="%s" stroke="%s" stroke-width="3"/>\n' % (JACKET, LINE)
    s += '  <path d="M372 600C388 640 396 700 398 800L352 800C354 720 356 656 344 604Z" fill="%s" stroke="%s" stroke-width="3"/>\n' % (JACKET_LT, LINE)
    s += '  <path d="M296 604C284 656 286 720 288 800" fill="none" stroke="%s" stroke-width="3.4" stroke-linecap="round"/>\n' % GOLD
    s += '  <path d="M344 604C356 656 354 720 352 800" fill="none" stroke="%s" stroke-width="3.4" stroke-linecap="round"/>\n' % GOLD
    s += '  <circle cx="262" cy="672" r="5" fill="%s" stroke="%s" stroke-width="1.8"/>\n' % (GOLD, GOLD_DK)
    s += '  <circle cx="378" cy="672" r="5" fill="%s" stroke="%s" stroke-width="1.8"/>\n' % (GOLD, GOLD_DK)
    s += '</g>\n'
    # ---------- face ----------
    s += '<g id="face">\n'
    s += ('  <path d="M320 236C264 236 232 288 232 344C232 404 252 452 278 484C292 502 306 514 320 514'
          'C334 514 348 502 362 484C388 452 408 404 408 344C408 288 376 236 320 236Z" '
          'fill="%s" stroke="%s" stroke-width="3.2" stroke-linejoin="round"/>\n' % (SKIN, LINE))
    s += '  <path d="M232 344C232 404 252 452 278 484C292 502 306 514 320 514C300 508 288 494 282 472C270 430 266 380 272 336Z" fill="%s" opacity=".55"/>\n' % SKIN_SH
    s += '</g>\n'
    # ---------- ears ----------
    s += '<g id="ears">\n'
    s += '  <path d="M234 366C216 358 202 374 204 396C206 420 220 440 238 436Z" fill="%s" stroke="%s" stroke-width="2.8" stroke-linejoin="round"/>\n' % (SKIN, LINE)
    s += '  <path d="M406 366C424 358 438 374 436 396C434 420 420 440 402 436Z" fill="%s" stroke="%s" stroke-width="2.8" stroke-linejoin="round"/>\n' % (SKIN, LINE)
    s += '  <path d="M228 380C218 378 212 388 214 400C216 414 226 424 234 424C226 408 222 392 228 380Z" fill="%s" opacity=".7"/>\n' % SKIN_SH
    s += '  <path d="M412 380C422 378 428 388 426 400C424 414 414 424 406 424C414 408 418 392 412 380Z" fill="%s" opacity=".7"/>\n' % SKIN_SH
    s += '</g>\n'
    # ---------- eyes ----------
    s += '<g id="eyes">\n'
    s += eye_group(258, 376, "clipEyeR", flip=-1, tag="eye-anatomical-right")
    s += eye_group(382, 376, "clipEyeL", flip=1, tag="eye-anatomical-left")
    s += '</g>\n'
    # ---------- brows ----------
    s += '<g id="brows">\n'
    s += brow_group(256, 320, flip=-1, tag="brow-anatomical-right")
    s += brow_group(384, 318, flip=1, tag="brow-anatomical-left")
    s += '</g>\n'
    # ---------- nose ----------
    s += '<g id="nose">\n'
    s += '  <path d="M322 398C320 410 318 418 320 424" fill="none" stroke="%s" stroke-width="3" stroke-linecap="round"/>\n' % SKIN_LN
    s += '  <ellipse cx="326" cy="408" rx="4" ry="2.6" fill="%s"/>\n' % WHITE
    s += '  <path d="M308 426C313 430 327 430 332 426" fill="none" stroke="%s" stroke-width="2.2" stroke-linecap="round" opacity=".8"/>\n' % SKIN_LN
    s += '</g>\n'
    # ---------- mouth ----------
    s += '<g id="mouth">\n'
    s += mouth_closed(320, 458, tag="mouth-closed-front")
    s += '</g>\n'
    # ---------- blush ----------
    s += '<g id="blush" opacity=".75">\n'
    for (bx, by) in [(258, 424), (268, 428), (248, 428), (382, 422), (392, 426), (372, 426)]:
        s += '  <circle cx="%d" cy="%d" r="2.6" fill="%s"/>\n' % (bx, by, BLUSH)
    s += '</g>\n'
    # ---------- ahoge (behind bangs so the root is hidden) ----------
    s += ahoge_group(322, 200, tag="ahoge")
    # ---------- front bangs ----------
    s += '<g id="hair-front-bangs">\n'
    s += ('  <path d="M210 300C212 244 252 192 320 192C388 192 428 238 436 290C439 302 427 307 420 296'
          'C412 268 392 246 362 238C346 266 324 300 302 324C295 333 283 327 288 314C278 331 263 344 249 350'
          'C240 354 233 346 238 335C227 341 215 333 219 322C213 316 208 308 210 300Z" '
          'fill="%s" stroke="%s" stroke-width="3.4" stroke-linejoin="round"/>\n' % (HAIR, LINE))
    s += '  <path d="M228 268C244 230 282 208 322 206C294 216 270 238 256 266C248 282 233 281 228 268Z" fill="%s" opacity=".9"/>\n' % HAIR_LT
    s += '  <path d="M232 302C258 288 300 268 340 246C366 232 392 234 412 250C390 242 366 244 342 258C302 280 262 302 232 302Z" fill="%s" opacity=".85"/>\n' % HAIR_SH
    s += '  <path d="M362 238C346 266 324 300 302 324C295 333 283 327 288 314C306 292 330 262 344 234Z" fill="%s" opacity=".8"/>\n' % HAIR_SH
    s += '  <path d="M300 206C330 200 364 212 388 234C360 218 330 212 302 216Z" fill="%s" opacity=".55"/>\n' % HAIR_HL
    s += '</g>\n'
    # ---------- side locks ----------
    s += '<g id="hair-side-locks">\n'
    s += ('  <path d="M212 292C198 326 192 370 196 410C199 438 208 456 221 460C230 462 234 452 228 442'
          'C219 425 215 400 217 374C220 338 230 312 243 294C234 288 220 287 212 292Z" '
          'fill="%s" stroke="%s" stroke-width="3" stroke-linejoin="round"/>\n' % (HAIR, LINE))
    s += '  <path d="M206 330C200 366 200 404 210 438C203 412 204 370 214 336Z" fill="%s" opacity=".8"/>\n' % HAIR_SH
    s += ('  <path d="M434 288C448 322 452 364 446 404C441 436 429 456 415 460C406 462 403 452 409 442'
          'C419 425 424 400 425 372C427 336 419 310 406 292C415 284 427 283 434 288Z" '
          'fill="%s" stroke="%s" stroke-width="3" stroke-linejoin="round"/>\n' % (HAIR, LINE))
    s += '  <path d="M436 330C442 366 442 404 432 440C439 412 438 370 428 336Z" fill="%s" opacity=".8"/>\n' % HAIR_SH
    s += '</g>\n'
    # ---------- gold crossed hairpin : anatomical LEFT = screen RIGHT ----------
    s += hairpin_group(424, 286, rot=-6, tag="gold-hairpin-anatomical-left")
    s += '</g>\n'
    s += '</svg>\n'
    return write_svg("view_000_front.svg", s)


def three_quarter_view():
    s = svg_open(640, 800, "0 0 640 800")
    s += '<g id="view-045" data-yaw="45">\n'
    # hair mass (skull turned: nose toward screen-right)
    s += '<g id="hair-back">\n'
    s += ('  <path d="M306 110C220 110 168 178 166 276C164 350 172 430 186 498C196 544 218 576 250 582'
          'C268 585 278 571 272 552C264 524 252 494 250 460C246 410 254 330 268 288C284 228 296 196 320 190'
          'C344 184 372 210 396 250C424 296 442 350 446 410C450 460 448 496 442 520C452 508 462 480 468 440'
          'C476 380 472 300 462 258C446 172 400 110 306 110Z" fill="%s" stroke="%s" stroke-width="3.5" stroke-linejoin="round"/>\n' % (HAIR, LINE))
    s += '  <path d="M190 420C200 496 220 554 252 578C262 584 270 576 268 564C256 530 246 494 244 452Z" fill="%s" opacity=".9"/>\n' % HAIR_SH
    s += '</g>\n'
    # hood + jacket + shirt + collar + bow (slight right shift)
    s += '<g id="hood">\n'
    s += ('  <path d="M336 556C256 556 190 596 152 656C132 684 124 714 120 744L180 744C184 700 198 662 226 636'
          'C252 610 292 594 336 594C380 594 418 610 444 636C472 662 486 700 490 744L550 744C546 714 538 684 520 656'
          'C484 596 416 556 336 556Z" fill="%s" stroke="%s" stroke-width="3.5" stroke-linejoin="round"/>\n' % (JACKET, LINE))
    s += '  <path d="M226 636C252 610 292 594 336 594C380 594 418 610 444 636" fill="none" stroke="%s" stroke-width="4.5" stroke-linecap="round"/>\n' % GOLD
    s += '</g>\n'
    s += '<g id="jacket">\n'
    s += ('  <path d="M336 566C262 566 202 596 162 638C130 672 112 730 104 800L568 800C560 730 542 672 510 638'
          'C470 596 410 566 336 566Z" fill="%s" stroke="%s" stroke-width="3.5" stroke-linejoin="round"/>\n' % (JACKET, LINE))
    s += '  <path d="M486 620C512 646 532 690 540 742L564 800L516 800C510 730 502 664 476 632Z" fill="%s" opacity=".85"/>\n' % JACKET_DK
    s += '</g>\n'
    s += '<g id="neck">\n'
    s += '  <path d="M300 458L298 542C298 568 370 568 370 542L368 458Z" fill="%s" stroke="%s" stroke-width="3"/>\n' % (SKIN, LINE)
    s += '  <path d="M300 458C306 508 362 508 368 458C362 496 306 496 300 458Z" fill="%s"/>\n' % SKIN_SH
    s += '</g>\n'
    s += '<g id="shirt">\n'
    s += '  <path d="M304 596L364 596L388 800L282 800Z" fill="%s" stroke="%s" stroke-width="3"/>\n' % (SHIRT, LINE)
    s += '  <path d="M364 596L388 800L368 800L352 596Z" fill="%s"/>\n' % SHIRT_SH
    s += '</g>\n'
    s += '<g id="collar">\n'
    s += '  <path d="M298 586L336 610L310 656L280 616Z" fill="%s" stroke="%s" stroke-width="3" stroke-linejoin="round"/>\n' % (SHIRT, LINE)
    s += '  <path d="M372 586L336 610L360 656L390 616Z" fill="%s" stroke="%s" stroke-width="3" stroke-linejoin="round"/>\n' % (SHIRT, LINE)
    s += '</g>\n'
    s += '<g id="bowtie">\n'
    s += '  <path d="M322 626C304 608 274 610 266 626C258 642 278 658 302 650C312 647 320 638 322 626Z" fill="%s" stroke="%s" stroke-width="2.6"/>\n' % (BOW, LINE)
    s += '  <path d="M350 626C368 608 398 610 406 626C414 642 394 658 370 650C360 647 352 638 350 626Z" fill="%s" stroke="%s" stroke-width="2.6"/>\n' % (BOW, LINE)
    s += '  <path d="M326 620C336 614 348 614 356 620C352 632 352 642 356 652C346 658 328 658 316 652C322 642 322 632 326 620Z" fill="%s" stroke="%s" stroke-width="2.6"/>\n' % (BOW, LINE)
    s += '  <path d="M324 652C316 676 314 700 320 722C330 706 336 690 336 668Z" fill="%s" stroke="%s" stroke-width="2.4"/>\n' % (BOW, LINE)
    s += '  <path d="M348 652C358 674 360 696 354 716C344 702 340 686 340 668Z" fill="%s" stroke="%s" stroke-width="2.4"/>\n' % (BOW_DK, LINE)
    s += '</g>\n'
    s += '<g id="jacket-front">\n'
    s += '  <path d="M282 600C266 640 258 700 256 800L302 800C300 720 298 656 310 604Z" fill="%s" stroke="%s" stroke-width="3"/>\n' % (JACKET, LINE)
    s += '  <path d="M388 600C404 640 412 700 414 800L368 800C370 720 372 656 360 604Z" fill="%s" stroke="%s" stroke-width="3"/>\n' % (JACKET_LT, LINE)
    s += '  <path d="M310 604C298 656 300 720 302 800" fill="none" stroke="%s" stroke-width="3.4" stroke-linecap="round"/>\n' % GOLD
    s += '  <path d="M360 604C372 656 370 720 368 800" fill="none" stroke="%s" stroke-width="3.4" stroke-linecap="round"/>\n' % GOLD
    s += '</g>\n'
    # face: turned to screen right
    s += '<g id="face">\n'
    s += ('  <path d="M330 234C288 238 258 288 254 342C250 400 266 452 292 484C304 502 316 514 330 514'
          'C346 514 364 500 376 478C392 448 400 404 400 352C400 290 372 228 330 234Z" '
          'fill="%s" stroke="%s" stroke-width="3.2" stroke-linejoin="round"/>\n' % (SKIN, LINE))
    s += '  <path d="M254 342C250 400 266 452 292 484C304 502 316 514 330 514C310 508 298 494 292 472C280 430 278 380 284 336Z" fill="%s" opacity=".5"/>\n' % SKIN_SH
    s += '</g>\n'
    # near ear (anatomical RIGHT) behind the near lock
    s += '<g id="ear-near">\n'
    s += '  <path d="M262 366C246 358 232 374 234 396C236 418 250 436 266 432Z" fill="%s" stroke="%s" stroke-width="2.8" stroke-linejoin="round"/>\n' % (SKIN, LINE)
    s += '  <path d="M256 380C246 378 240 388 242 400C244 414 252 424 260 424C252 408 250 392 256 380Z" fill="%s" opacity=".7"/>\n' % SKIN_SH
    s += '</g>\n'
    # eyes: near eye = anatomical right (screen-left of nose), far eye = anatomical left (narrowed)
    s += '<g id="eyes">\n'
    s += eye_group(296, 374, "clipEyeNear45", flip=-1, sx=0.94, tag="eye-anatomical-right")
    s += eye_group(360, 370, "clipEyeFar45", flip=1, sx=0.62, tag="eye-anatomical-left")
    s += '</g>\n'
    s += '<g id="brows">\n'
    s += brow_group(294, 318, flip=-1, tag="brow-anatomical-right")
    s += brow_group(358, 314, flip=1, tag="brow-anatomical-left")
    s += '</g>\n'
    # 3/4 nose: bridge curve, tip, nostril on the far-left side of the tip
    s += '<g id="nose">\n'
    s += '  <path d="M378 368C378 384 380 396 388 404C394 410 392 418 384 420C376 421 372 416 372 409" fill="none" stroke="%s" stroke-width="3" stroke-linecap="round"/>\n' % SKIN_LN
    s += '  <path d="M374 412C378 416 384 417 388 415" fill="none" stroke="%s" stroke-width="2.4" stroke-linecap="round"/>\n' % SKIN_LN
    s += '  <ellipse cx="386" cy="392" rx="4" ry="2.6" fill="%s" transform="rotate(20 386 392)"/>\n' % WHITE
    s += '</g>\n'
    s += '<g id="mouth">\n'
    s += mouth_closed(360, 456, scale=0.92, tag="mouth-closed-45")
    s += '</g>\n'
    s += '<g id="blush" opacity=".7">\n'
    s += '  <circle cx="312" cy="422" r="2.6" fill="%s"/>\n' % BLUSH
    s += '  <circle cx="302" cy="426" r="2.4" fill="%s"/>\n' % BLUSH
    s += '  <circle cx="382" cy="418" r="2.4" fill="%s"/>\n' % BLUSH
    s += '</g>\n'
    # ahoge
    s += ahoge_group(330, 206, tag="ahoge")
    # bangs swept, parting off-center
    s += '<g id="hair-front-bangs">\n'
    s += ('  <path d="M208 306C210 248 250 196 316 194C382 192 424 236 434 292C437 304 425 309 418 298'
          'C410 270 392 248 366 240C352 264 336 288 316 306C302 319 286 316 292 302C280 318 266 330 252 336'
          'C242 340 235 332 240 322C229 328 217 320 221 310C214 316 206 312 208 306Z" '
          'fill="%s" stroke="%s" stroke-width="3.4" stroke-linejoin="round"/>\n' % (HAIR, LINE))
    s += '  <path d="M228 272C244 232 282 208 322 206C296 216 272 238 258 268C250 284 233 282 228 272Z" fill="%s" opacity=".9"/>\n' % HAIR_LT
    s += '  <path d="M366 240C352 264 336 288 316 306C302 319 286 316 292 302C308 282 330 258 346 234Z" fill="%s" opacity=".8"/>\n' % HAIR_SH
    s += '  <path d="M240 306C268 290 306 268 344 248C370 234 394 238 412 252C390 244 368 246 344 258C308 278 268 306 240 306Z" fill="%s" opacity=".8"/>\n' % HAIR_SH
    s += '</g>\n'
    # near side lock (character's right side) over the ear
    s += '<g id="hair-side-locks">\n'
    s += ('  <path d="M240 296C228 328 224 366 228 402C231 430 240 450 252 454C261 456 264 447 258 438'
          'C249 422 246 400 248 378C250 348 258 320 268 300C260 292 248 291 240 296Z" '
          'fill="%s" stroke="%s" stroke-width="3" stroke-linejoin="round"/>\n' % (HAIR, LINE))
    s += '  <path d="M234 330C230 362 230 398 240 432C232 404 234 366 244 334Z" fill="%s" opacity=".8"/>\n' % HAIR_SH
    s += ('  <path d="M416 280C432 310 440 348 438 386C436 414 428 436 416 444C408 449 406 440 412 432'
          'C422 418 426 396 424 372C422 340 414 310 402 288C406 282 412 278 416 280Z" '
          'fill="%s" stroke="%s" stroke-width="3" stroke-linejoin="round"/>\n' % (HAIR, LINE))
    s += '</g>\n'
    # far-side (anatomical LEFT) gold pin: mostly hidden behind the far hair mass
    s += hairpin_group(240, 262, rot=24, scale=0.8, tag="gold-hairpin-far-occluded")
    s += ('  <path d="M212 292C204 318 202 344 206 368C214 340 222 316 232 298Z" fill="%s" stroke="%s" stroke-width="2.6"/>\n' % (HAIR, LINE))
    s += '</g>\n'
    s += '</svg>\n'
    return write_svg("view_045_three_quarter_right.svg", s)


if __name__ == "__main__":
    print(front_view())
    print(three_quarter_view())
