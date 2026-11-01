"""View 090 (true right profile) and View 180 (back of head + garment back).
Camera convention (identity_spec): yaw +45 -> +90 moves the character's nose
toward screen-right, exposing the character's RIGHT side (so in 090 the visible
eye/ear are the anatomical right ones; the gold cross hairpin stays on the
character's anatomical LEFT = the far side, only a sliver peeking out).
"""
from common import *


def profile_view():
    s = svg_open(640, 800, "0 0 640 800")
    s += '<g id="view-090" data-yaw="90">\n'
    # ---------------- torso / jacket (side) ----------------
    s += '<g id="jacket">\n'
    s += ('  <path d="M300 566C226 566 168 598 130 640C100 674 84 730 76 800L566 800C558 730 540 676 506 644'
          'C470 606 404 566 356 560Z" fill="%s" stroke="%s" stroke-width="3.5" stroke-linejoin="round"/>\n' % (JACKET, LINE))
    s += '  <path d="M470 612C504 640 524 688 532 742L556 800L500 800C494 728 486 660 456 626Z" fill="%s" opacity=".85"/>\n' % JACKET_DK
    s += '  <path d="M356 560C404 566 470 606 506 644C472 622 420 600 356 594Z" fill="%s" opacity=".6"/>\n' % JACKET_LT
    s += '</g>\n'
    # hood behind the neck
    s += '<g id="hood">\n'
    s += ('  <path d="M300 552C234 552 176 590 144 644C126 672 116 702 112 732L166 732C170 692 184 658 210 634'
          'C236 610 268 598 300 598C332 598 364 610 390 634C416 658 430 692 434 732L488 732C484 702 474 672 456 644'
          'C424 590 366 552 300 552Z" fill="%s" stroke="%s" stroke-width="3.5" stroke-linejoin="round"/>\n' % (JACKET, LINE))
    s += '  <path d="M210 634C236 610 268 598 300 598C332 598 364 610 390 634" fill="none" stroke="%s" stroke-width="4.5" stroke-linecap="round"/>\n' % GOLD
    s += '</g>\n'
    # ---------------- neck ----------------
    s += '<g id="neck">\n'
    s += '  <path d="M300 430L296 548C296 574 356 574 356 548L360 440Z" fill="%s" stroke="%s" stroke-width="3"/>\n' % (SKIN, LINE)
    s += '  <path d="M300 430C306 478 356 486 360 440C356 478 306 462 300 430Z" fill="%s"/>\n' % SKIN_SH
    s += '</g>\n'
    # ---------------- back hair mass ----------------
    s += '<g id="hair-back">\n'
    s += ('  <path d="M472 258C436 216 374 190 322 192C262 194 224 240 218 302C212 366 216 438 230 494'
          'C238 528 254 552 278 560C298 566 314 552 310 536C304 516 294 500 290 474C286 438 290 378 298 330'
          'C306 284 330 252 356 238C384 222 420 230 444 248C458 258 468 266 472 258Z" '
          'fill="%s" stroke="%s" stroke-width="3.5" stroke-linejoin="round"/>\n' % (HAIR, LINE))
    s += '  <path d="M236 418C242 484 258 534 282 556C292 562 300 556 298 546C288 514 280 476 280 444Z" fill="%s" opacity=".85"/>\n' % HAIR_SH
    s += '  <path d="M246 268C272 220 322 198 368 204C330 210 296 232 278 262C268 280 250 280 246 268Z" fill="%s" opacity=".85"/>\n' % HAIR_LT
    s += '</g>\n'
    # ---------------- face (true profile silhouette) ----------------
    s += '<g id="face-profile">\n'
    s += ('  <path d="M448 256C472 292 476 322 472 344C472 357 478 370 492 386C500 394 498 405 485 408'
          'C475 410 468 414 466 423C471 429 470 435 462 439C467 445 465 453 457 459C447 471 425 481 401 487'
          'C375 493 349 482 334 462C320 443 312 420 312 396C312 340 330 288 372 266C398 252 428 248 448 256Z" '
          'fill="%s" stroke="%s" stroke-width="3.2" stroke-linejoin="round"/>\n' % (SKIN, LINE))
    s += '  <path d="M320 440C330 468 356 490 390 492C364 502 334 490 322 466C314 450 314 442 320 440Z" fill="%s" opacity=".55"/>\n' % SKIN_SH
    s += '  <path d="M430 250C446 246 462 252 472 266C460 258 446 256 434 262Z" fill="%s" opacity=".5"/>\n' % SKIN_SH
    s += '</g>\n'
    # ---------------- ear (anatomical right, with hidden root) ----------------
    s += '<g id="ear-profile">\n'
    s += '  <path d="M318 300C344 292 368 304 372 330C376 356 368 394 352 420C340 438 322 438 314 420C306 400 306 344 312 314Z" fill="%s" stroke="%s" stroke-width="3" stroke-linejoin="round"/>\n' % (SKIN, LINE)
    s += '  <path d="M330 318C344 312 356 320 358 336C360 352 354 376 344 396C336 412 324 412 320 398C316 380 318 332 330 318Z" fill="%s" opacity=".75"/>\n' % SKIN_SH
    s += '  <path d="M336 330C346 326 352 336 350 350C348 366 340 380 332 384C338 366 340 344 336 330Z" fill="%s" opacity=".8"/>\n' % SKIN_LN
    s += '  <path d="M306 296C328 286 352 296 360 318C340 304 322 306 310 316Z" fill="%s" opacity=".55"/>\n' % SKIN_SH
    s += '</g>\n'
    # ---------------- profile eye (anatomical right, foreshortened) ----------------
    s += '<g id="eye-profile">\n'
    s += '  <path d="M424 352C432 336 452 328 468 334C478 338 482 348 478 356C470 366 446 372 430 366C424 363 421 357 424 352Z" fill="%s" stroke="%s" stroke-width="2.2"/>\n' % (WHITE, LINE)
    s += '  <ellipse cx="462" cy="349" rx="11" ry="14" fill="%s"/>\n' % IRIS
    s += '  <ellipse cx="462" cy="347" rx="11" ry="13" fill="%s"/>\n' % IRIS_DK
    s += '  <ellipse cx="462" cy="351" rx="9.5" ry="11" fill="%s"/>\n' % IRIS
    s += '  <ellipse cx="462" cy="349" rx="3.6" ry="8" fill="%s"/>\n' % PUPIL
    s += '  <circle cx="458" cy="341" r="3.6" fill="%s"/>\n' % WHITE
    s += '  <circle cx="466" cy="357" r="1.9" fill="%s" opacity=".9"/>\n' % WHITE
    s += '  <path d="M420 348C428 332 450 324 468 330C480 334 486 344 482 356L477 356C478 346 472 338 462 336C446 332 432 340 426 352Z" fill="%s"/>\n' % LASH
    s += '  <path d="M478 352C486 350 494 344 500 338C494 348 486 356 479 358Z" fill="%s"/>\n' % LASH
    s += '  <path d="M428 368C440 376 458 378 472 372" fill="none" stroke="%s" stroke-width="2.2" stroke-linecap="round"/>\n' % LASH
    s += '  <path d="M420 328C436 314 462 312 476 322" fill="none" stroke="%s" stroke-width="4.2" stroke-linecap="round"/>\n' % HAIR_SH
    s += '</g>\n'
    # ---------------- nose / mouth / chin detail ----------------
    s += '<g id="nose-profile">\n'
    s += '  <path d="M472 350C474 362 480 374 490 384" fill="none" stroke="%s" stroke-width="2.4" stroke-linecap="round" opacity=".8"/>\n' % SKIN_LN
    s += '  <path d="M482 402C487 404 492 403 494 399" fill="none" stroke="%s" stroke-width="2.6" stroke-linecap="round"/>\n' % SKIN_LN
    s += '  <path d="M484 396C489 396 492 393 493 389" fill="none" stroke="%s" stroke-width="2.4" stroke-linecap="round"/>\n' % SKIN_LN
    s += '  <ellipse cx="488" cy="386" rx="4" ry="2.6" fill="%s" transform="rotate(35 488 386)"/>\n' % WHITE
    s += '</g>\n'
    s += '<g id="mouth-profile">\n'
    s += '  <path d="M470 430C462 433 450 436 440 437C450 441 462 440 470 436Z" fill="#E7A8A0" stroke="#A65A62" stroke-width="2.2" stroke-linejoin="round"/>\n'
    s += '  <path d="M466 433C458 436 448 438 441 437" fill="none" stroke="#A65A62" stroke-width="2"/>'
    s += '  <path d="M452 444C458 446 464 445 468 442" fill="none" stroke="#F0C4BC" stroke-width="2.2" stroke-linecap="round"/>\n'
    s += '</g>\n'
    s += '<g id="blush" opacity=".65"><circle cx="440" cy="404" r="3" fill="%s"/><circle cx="428" cy="408" r="2.4" fill="%s"/></g>\n' % (BLUSH, BLUSH)
    # ---------------- front hair: bangs + side lock + nape strands ----------------
    s += '<g id="hair-front">\n'
    s += ('  <path d="M462 250C436 222 392 206 348 210C316 214 296 234 288 262C296 250 312 244 328 246'
          'C318 266 320 292 336 310C346 322 356 316 352 302C348 286 350 268 358 256C376 268 392 288 402 314'
          'C406 326 418 326 418 314C418 296 412 274 404 258C424 258 444 254 462 250Z" '
          'fill="%s" stroke="%s" stroke-width="3.2" stroke-linejoin="round"/>\n' % (HAIR, LINE))
    s += '  <path d="M300 258C312 238 332 224 352 218C328 226 312 240 304 258C298 270 292 266 300 258Z" fill="%s" opacity=".8"/>\n' % HAIR_LT
    s += '  <path d="M352 254C370 266 386 286 396 312C388 288 372 268 352 258Z" fill="%s" opacity=".75"/>\n' % HAIR_SH
    s += ('  <path d="M392 262C404 300 404 350 396 396C390 432 378 460 366 470C358 476 354 468 360 458'
          'C370 440 378 414 380 384C384 340 380 296 370 268C376 260 386 258 392 262Z" '
          'fill="%s" stroke="%s" stroke-width="2.8" stroke-linejoin="round"/>\n' % (HAIR, LINE))
    s += '  <path d="M386 276C394 312 394 356 388 396C396 356 396 312 390 282Z" fill="%s" opacity=".8"/>\n' % HAIR_SH
    s += ('  <path d="M292 300C280 336 278 384 286 424C290 444 278 452 270 436C258 412 256 364 266 322'
          'C270 308 282 294 292 300Z" fill="%s" stroke="%s" stroke-width="2.8" stroke-linejoin="round"/>\n' % (HAIR, LINE))
    s += '</g>\n'
    # ---------------- gold hairpin: anatomical LEFT = far side, sliver only ----------------
    s += hairpin_group(430, 252, rot=28, scale=0.62, tag="gold-hairpin-far-side-sliver")
    # near-side hair overlaps most of the pin -> only a tip shows
    s += '  <path d="M404 236C424 244 442 262 452 286C436 266 418 254 398 250Z" fill="%s" stroke="%s" stroke-width="2.6" stroke-linejoin="round"/>\n' % (HAIR, LINE)
    # ---------------- ahoge (single, curving to the camera side) ----------------
    s += ahoge_group(322, 200, scale=0.92, rot=16, tag="ahoge")
    s += '</g>\n'
    s += '</svg>\n'
    return write_svg("view_090_profile_right.svg", s)


def back_view():
    s = svg_open(640, 800, "0 0 640 800")
    s += '<g id="view-180" data-yaw="180">\n'
    # ---------------- jacket back ----------------
    s += '<g id="jacket-back">\n'
    s += ('  <path d="M320 566C246 566 184 598 142 640C108 676 92 732 84 800L556 800C548 732 532 676 498 640'
          'C456 598 394 566 320 566Z" fill="%s" stroke="%s" stroke-width="3.5" stroke-linejoin="round"/>\n' % (JACKET, LINE))
    s += '  <path d="M142 640C168 616 204 596 246 586C206 604 174 626 156 654C138 682 128 720 124 756L96 756C102 716 116 670 142 640Z" fill="%s" opacity=".8"/>\n' % JACKET_DK
    s += '  <path d="M498 640C472 616 436 596 394 586C434 604 466 626 484 654C502 682 512 720 516 756L544 756C538 716 524 670 498 640Z" fill="%s" opacity=".55"/>\n' % JACKET_LT
    s += '  <path d="M320 590C288 590 262 604 246 626C272 612 294 606 320 606C346 606 368 612 394 626C378 604 352 590 320 590Z" fill="%s" stroke="%s" stroke-width="3"/>\n' % (SHIRT, LINE)
    s += '</g>\n'
    # ---------------- hood over the shoulders ----------------
    s += '<g id="hood-back">\n'
    s += ('  <path d="M320 548C250 548 186 588 152 642C132 670 122 702 118 734L174 734C178 694 192 660 218 636'
          'C242 612 278 600 320 600C362 600 398 612 422 636C448 660 462 694 466 734L522 734C518 702 508 670 488 642'
          'C454 588 390 548 320 548Z" fill="%s" stroke="%s" stroke-width="3.5" stroke-linejoin="round"/>\n' % (JACKET, LINE))
    s += '  <path d="M218 636C242 612 278 600 320 600C362 600 398 612 422 636" fill="none" stroke="%s" stroke-width="4.5" stroke-linecap="round"/>\n' % GOLD
    s += '  <path d="M320 548C288 548 258 562 236 584C262 570 290 564 320 564C350 564 378 570 404 584C382 562 352 548 320 548Z" fill="%s" opacity=".65"/>\n' % JACKET_LT
    s += '</g>\n'
    # ---------------- neck (nape) ----------------
    s += '<g id="neck-back">\n'
    s += '  <path d="M282 470L280 566C280 588 360 588 360 566L358 470Z" fill="%s" stroke="%s" stroke-width="3"/>\n' % (SKIN, LINE)
    s += '  <path d="M282 470C292 506 348 506 358 470C350 496 290 494 282 470Z" fill="%s"/>\n' % SKIN_SH
    s += '</g>\n'
    # ---------------- back of head hair ----------------
    s += '<g id="hair-back-head">\n'
    s += ('  <path d="M320 110C230 110 176 180 174 276C172 348 180 424 192 486C200 528 220 560 248 572'
          'C266 580 280 566 274 548C266 524 256 496 254 462C252 408 258 336 270 296C284 250 300 226 320 222'
          'C340 226 356 250 370 296C382 336 388 408 386 462C384 496 374 524 366 548C360 566 374 580 392 572'
          'C420 560 440 528 448 486C460 424 468 348 466 276C464 180 410 110 320 110Z" '
          'fill="%s" stroke="%s" stroke-width="3.5" stroke-linejoin="round"/>\n' % (HAIR, LINE))
    s += '  <path d="M196 410C204 476 222 540 252 566C262 572 270 564 266 552C252 516 244 476 244 440Z" fill="%s" opacity=".9"/>\n' % HAIR_SH
    s += '  <path d="M444 410C436 476 418 540 388 566C378 572 370 564 374 552C388 516 396 476 396 440Z" fill="%s" opacity=".9"/>\n' % HAIR_SH
    s += '  <path d="M242 262C266 214 316 190 362 196C324 202 290 224 272 254C262 272 246 272 242 262Z" fill="%s" opacity=".85"/>\n' % HAIR_LT
    # layered pointed ends at the nape
    s += ('  <path d="M262 388C252 434 252 486 264 524C270 544 282 552 290 544C278 520 274 484 278 450'
          'C282 414 292 384 306 364C292 366 272 372 262 388Z" fill="%s" stroke="%s" stroke-width="2.8" stroke-linejoin="round"/>\n' % (HAIR, LINE))
    s += ('  <path d="M378 388C388 434 388 486 376 524C370 544 358 552 350 544C362 520 366 484 362 450'
          'C358 414 348 384 334 364C348 366 368 372 378 388Z" fill="%s" stroke="%s" stroke-width="2.8" stroke-linejoin="round"/>\n' % (HAIR, LINE))
    s += ('  <path d="M300 400C294 446 296 496 306 532C312 552 326 556 330 540C320 508 316 466 320 424'
          'C324 396 336 376 348 366C330 364 310 376 300 400Z" fill="%s" stroke="%s" stroke-width="2.8" stroke-linejoin="round"/>\n' % (HAIR_SH, LINE))
    s += '</g>\n'
    # ---------------- ahoge (single strand, leans to the character's right = screen-right from behind) ----------------
    s += ahoge_group(334, 196, scale=0.86, rot=22, tag="ahoge")
    # ---------------- gold hairpin: anatomical LEFT = screen-left seen from behind ----------------
    s += hairpin_group(238, 268, rot=-34, scale=0.6, tag="gold-hairpin-left-side")
    s += '  <path d="M236 240C224 264 222 292 228 320C236 292 244 268 252 252C248 244 242 238 236 240Z" fill="%s" stroke="%s" stroke-width="2.6" stroke-linejoin="round"/>\n' % (HAIR, LINE)
    s += '</g>\n'
    s += '</svg>\n'
    return write_svg("view_180_back.svg", s)


if __name__ == "__main__":
    print(profile_view())
    print(back_view())
